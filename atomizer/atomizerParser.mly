%{
open Core
open Printf
open Ast
open Utils

let parse_error s = printf "Parse Error: %s"

let mk_point_val_f_opt (s: string option) = 
  match s with
  | None -> (None, "None")
  | Some x -> (Some (float_of_string x), "Some " ^ x)

%}	

%token EOF

%token <string> COMMENT_LINE
%token <string> NEWLINE
%token <string> HSPACE
%token <string> NSCHAR
%token <string> ENV

%token <string * string option> KW_CHAPTER
%token <string * string option> KW_SECTION
%token <string * string option> KW_SUBSECTION
%token <string * string option> KW_SUBSUBSECTION	
%token <string * string option> KW_PARAGRAPH	

%start chapter
%type <string> chapter

/*  BEGIN RULES */
%%

/**********************************************************************
 ** BEGIN: Lines, Textparagraphs, and environments
 **********************************************************************/

hspace: 
  s = HSPACE
  {s}

hspaces: 
  {""}
| xs = hspaces;
  x = HSPACE;
  {xs ^ x}

hchar: 
  s = HSPACE
  {s}
| c = NSCHAR
  {c} 

hchars: 
  {""}
| xs = hchars;
  x = hchar
  {x ^ xs}

/* A newline. */
newline: 
  nl = NEWLINE
  {nl}

/* An empty line. */
emptyline: 
  s = hspaces;
  nl = newline
  {s ^ nl}

emptylines:
  {""}
| els = emptylines;
  el = emptyline
  {let _ = d_printf "!Parser mached: emptylines.\n" in
     els; el
   }

/* A nonempty line. */
line: 
  hs = hspaces;
  nsc = NSCHAR;
  hcs = hchars;
  nl = newline
  {hs ^ nsc ^ hcs ^ nl}

/* A latex environment. */
env: 
  x = ENV
  {x}  

/* A text paragraph. */
textpar: 
  x = line;
  y = emptyline
  {x ^ y}  
| x = line;
  tp = textpar
  { 
    x ^ tp
  } 

comments:
  x = COMMENT_LINE
  {d_printf "!parser matched: comment line\n";
   x 
  }
| x = COMMENT_LINE;  
  y = comments
  { x ^ y}

commentpar:
  x = comments;
  el = emptyline;
  {let _ = d_printf "parser matched: commentpar.\n" in
     x ^ el 
  }

commentpars:
  xs = commentpars;
  els = emptylines;
  x = commentpar;
  { 
    xs ^ els ^ x
  }

ignorables:
  els_f = emptylines; 
  cps = commentpars;
  els_t = emptylines
  {let _ = d_printf "parser mached: ignorables: emptylines + commentpars + emptylines\n" in
     els_f ^ cps ^ els_t
  }
/**********************************************************************
 ** BEGIN: Latex Sections
 **********************************************************************/
/* Return  heading and title pair. */ 
mk_heading(kw_heading):
  h = kw_heading
  {let (heading, pval_opt) = h in 
   let (pval_f_opt, pval_opt_str) = mk_point_val_f_opt pval_opt in
     (heading, pval_f_opt) 
  }

mk_section(kw_section, nested_section):
  h = mk_heading(kw_section); 
  b = block;
  ps = paragraphs;
  ns = mk_sections(nested_section);
  {
   let (heading, pval_opt) = h in
   let _ = d_printf ("!parser: section %s matched") heading in
     heading ^ ps ^ ns
  }	  

mk_sections(my_section):
|  {""}
| ss = mk_sections(my_section); s = my_section
  {ss ^ s}

chapter:
  h = mk_heading(KW_CHAPTER); 
  b = block; 
  ps = paragraphs;
  ss = mk_sections(section); 
  EOF 
  {
   let (heading, pval_opt) = h in
     heading ^
     b ^
     ps ^
     ss
  }	

section: 
  s = mk_section(KW_SECTION, subsection)
  {
   s   
  }	  

subsection: 
  s = mk_section(KW_SUBSECTION, subsubsection)
  {
   s
  }	  	

subsubsection:
  h = mk_heading(KW_SUBSUBSECTION); 
  b = block;
  ps = paragraphs;
  {
   let (heading, pval_opt) = h in
     heading ^ 
     b ^
     ps
  }	  

paragraph:  
  h = mk_heading(KW_PARAGRAPH); 
  b = block;
  {
   let _ = d_printf ("Parser matched: paragraph.\n") in
   let (heading, pval_opt) = h in
     heading ^ b 
  }	  

paragraphs:
| 
 { "" }
| p = paragraph; 
  ps = paragraphs;
  {ps ^ p}

/**********************************************************************
 ** END: Latex Sections
 **********************************************************************/

/**********************************************************************
 ** BEGIN: Blocks
 ** A blocks is  sequence of atoms/groups followed by paragraphs
 **********************************************************************/

block: 
| es = elements; 
  tt = ignorables;
  {
   let _ = d_printf ("parser matched: blocks.\n") in 
     es ^ tt
  }

/**********************************************************************
 ** END: Blocks
 **********************************************************************/

/**********************************************************************
 ** BEGIN: Elements
 ** An element is a group, a problem cluster, or an atom 
 **********************************************************************/

element:
  ft = ignorables;
	e = env;  
  {ft ^ e}
| ft = ignorables;
  tp = textpar;
  {ft ^ "\\begin{gram}" ^ "\n" ^ tp ^ "\n" ^ "\\end{gram}"}

elements:
  {""}
| es = elements;
  e = element; 
  {es ^ e}

/**********************************************************************
 ** END: Elements
 **********************************************************************/
