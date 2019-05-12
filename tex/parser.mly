%{
open Core
open Printf
open Ast
open Utils

let parse_error s = printf "Parse Error: %s"
let kw_atom_definition = "definition"

let sections_option vo = 
  match vo with 
  |	None -> []
  |	Some v -> v

let blocks_option vo = 
  match vo with 
  |	None -> []
  |	Some v -> v

let element_option vo = 
  match vo with 
  |	None -> []
  |	Some v -> v


let mk_point_val_f_opt (s: string option) = 
  match s with
  | None -> (None, "None")
  | Some x -> (Some (float_of_string x), "Some " ^ x)

%}	

%token EOF

%token <string> WORD
%token <string> ENV

/* A hint is heading, body, solution option, explain option, rubric oction, ending */
%token <string * string * string option * string option * string option * (string * string)> HINT

/* A ref sol is heading, body, explain option, rubric option, ending */
%token <string * string * string option * string option * (string * string)> REFSOL 

/* A rubric is heading, body, ending */
%token <string * string * (string * string)> RUBRIC

/* ilist is 
 * kind * kw_begin * point-value option * (item-separator-keyword, point value option, item-body) list * kw_end list 
 */
%token <string * string * (string * string * string) option * ((string * string option * string) list) * string> ILIST

%token <string> BACKSLASH
%token <string> PERCENT  /* latex special \% */
%token <string> O_CURLY C_CURLY	
%token <string> O_SQ_BRACKET C_SQ_BRACKET
%token <string> COMMENT_LINE

%token <string * string * string option> KW_BEGIN_ATOM
%token <string * string> KW_END_ATOM 
%token <string> KW_LABEL
%token <string * string list * string> KW_DEPEND
%token <string * string> KW_LABEL_AND_NAME

%token <string> KW_CHAPTER
%token <string> KW_SECTION
%token <string> KW_SUBSECTION
%token <string> KW_SUBSUBSECTION	
%token <string> KW_PARAGRAPH	

/* cluster is heading and point value option */
%token <string * string option> KW_BEGIN_CLUSTER 
%token <string> KW_END_CLUSTER

/*%token <string> KW_BEGIN_GROUP KW_END_GROUP */

%token <string * string * string option> KW_BEGIN_GROUP
%token <string * string> KW_END_GROUP 	
%start chapter

%type <Ast.chapter> chapter
%type <Ast.section> section
%type <Ast.subsection> subsection
%type <Ast.subsubsection> subsubsection
%type <Ast.group> group
%type <Ast.atom> atom

/*  BEGIN RULES */
%%

/**********************************************************************
 ** BEGIN: Words and Boxes 
 **********************************************************************/

/* A curly box looks like
   { word } 
   { [ word ] { word } ] 
   etc.  
*/
curly_box:
  o = O_CURLY;  b = boxes;  c = C_CURLY 
  {(o, b, c)}

sq_box:
  o = O_SQ_BRACKET; b = boxes;  c = C_SQ_BRACKET 
  {(o, b, c)}
 
word: 
  w = WORD 
  {w}
| x = COMMENT_LINE
  {x}
| bone = BACKSLASH btwo = BACKSLASH  /* latex special: // */
  {bone ^ btwo}
| b = BACKSLASH c = O_CURLY  /* latex special: \{ */
  {b ^ c}
| b = BACKSLASH c = C_CURLY /* latex special: \} */
  {b ^ c}
| b = BACKSLASH s = O_SQ_BRACKET  /* latex special: \[ */
  {b ^ s}
| b = BACKSLASH s = C_SQ_BRACKET /* latex special: \] */
  {b ^ s}
| x = PERCENT /* latex special: \% */
  {x}
| b = BACKSLASH w = WORD
  {b ^ w}

env: 
  x = ENV
  {x}  

blob:
  x = env
  {let _ = d_printf ("!parser: blob/env matched = %s\n.") x in
     x
  }
| x = word
  {x}

/* a box is the basic unit of composition */
box:
  x = blob
  {x}
| b = curly_box 
  {let (bo, bb, bc) = b in bo ^ bb ^ bc}
| b = sq_box 
  {let (bo, bb, bc) = b in bo ^ bb ^ bc}

boxes:
  {""}
| bs = boxes; b = box
  {bs ^ b }

boxes_start_no_sq:
  {""}
|	x = blob; bs = boxes
  {x ^ bs}
|	b = curly_box; bs = boxes
  {let (bo, bb, bc) = b in bo ^ bb ^ bc ^ bs }

/* I don't think hints should have a preamble, because
   it is in inside of diderot atoms */
hint:
| hi = HINT
  {let (h_b, body, sol_opt, exp_opt, rubric_opt, h_e) = hi in
   let _ = d_printf ("!parser: hint matched") in     
     (h_b, body, sol_opt, exp_opt, rubric_opt, h_e)
  }

/* I don't think solutions should have a preamble, because
   it is in inside of diderot atoms */
refsol:
| s = REFSOL
  {let (h_b, body, exp_opt, rubric_opt, h_e) = s in
   let _ = d_printf ("!parser: refsol matched") in     
     (h_b, body, exp_opt, rubric_opt, h_e)
  }


/* I don't think ilist should have a preamble, because
   it is in inside of diderot atoms */
ilist:
| il = ILIST
  {let (kind, kw_b, arg_opt, ilist, kw_e) = il in
   let ilist = List.map ilist ~f:(fun (x, pval, y) -> (x, fst (mk_point_val_f_opt pval), y)) in
   let items = List.map ilist ~f:(fun (x, pval, y) -> Ast.mk_item (x, pval, y)) in
   let _ = d_printf ("!parser: ilist matched") in
     match arg_opt with
     | None -> 
         Ast.IList ("", (kind, kw_b, None, items, kw_e))
     | Some (o_s, point_val, c_s) -> 
       let kw_b_all = kw_b ^ o_s ^ point_val ^ c_s in
       let point_val_f = float_of_string point_val in
         Ast.IList ("", (kind, kw_b_all, Some point_val_f, items, kw_e))        
  }

/**********************************************************************
 ** END: Words and Boxes 
 **********************************************************************/

/**********************************************************************
 ** BEGIN: Diderot Keywords
 **********************************************************************/
/* Return full text "\label{label_string}  \n" plus label */
/*
label:
  l = KW_LABEL; b = curly_box 
  {let (bo, bb, bc) = b in 
   let h = l ^ bo ^ bb ^ bc in
     Ast.Label(h, bb)}
*/
label:
  l = KW_LABEL_AND_NAME
  {let (all, label) = l in 
   let _ = d_printf "Parser matched label = %s all = %s" label all in
     Ast.Label(all, label)}

depend:
  d = KW_DEPEND
  {let (hb, ds, he) = d in      
     Ast.Depend (hb, ds)
  }

/**********************************************************************
 ** END Diderot Keywords
 **********************************************************************/

/**********************************************************************
 ** BEGIN: Latex Sections
 **********************************************************************/
/* Return  heading and title pair. */ 
mk_heading(kw_heading):
  hc = kw_heading; b = curly_box 
  {let (bo, bb, bc) = b in (hc ^ bo ^ bb ^ bc, bb) }

mk_section(kw_section, nested_section):
  h = mk_heading(kw_section); 
  l = option(label); 
  bs = blocks;
  nso = option(mk_sections(nested_section));
  {
   let (heading, t) = h in
   let _ = d_printf ("!parser: section %s matched") heading in
   let ns = sections_option nso in
   let tt = "" in
     (heading, t, l, bs, tt, ns)
  }	  

mk_sections(my_section):
| s = my_section; {[s]}
| ss = mk_sections(my_section); s = my_section
  {List.append ss [s]}

chapter:
  preamble = boxes;
  h = mk_heading(KW_CHAPTER); 
  l = label; 
  bs = blocks; 
  sso = option(mk_sections(section)); 
  EOF 
  {
   let (heading, t) = h in
   let ss = sections_option sso in
   let tt = "" in
     Ast.Chapter(preamble, (heading, t, l, bs, tt, ss))
  }	

section: 
  desc = mk_section(KW_SECTION, subsection)
  {
     Ast.Section desc
  }	  

subsection: 
  desc = mk_section(KW_SUBSECTION, subsubsection)
  {
     Ast.Subsection desc
  }	  	

subsubsection:
  h = mk_heading(KW_SUBSUBSECTION); 
  l = option(label); 
  bs = blocks;
  {
   let (heading, t) = h in
   let tt = "" in
     Ast.Subsubsection (heading, t, l, bs, tt)
  }	  

paragraph:  
  h = mk_heading(KW_PARAGRAPH); 
  l = option(label); 
  es = elements;
  {
   let _ = d_printf ("Parser matched: paragraph.\n") in
   let (heading, t) = h in
   let tt = "" in
     Ast.Paragraph (heading, None, t, l, es, tt) 
  }	  

paragraphs:
| p = paragraph;
  { [p] }
| p = paragraph; 
  ps = paragraphs;
  {List.append ps [p]}

/**********************************************************************
 ** END: Latex Sections
 **********************************************************************/

/**********************************************************************
 ** BEGIN: Blocks
 ** A blocks is  sequence of atoms/groups followed by paragraphs
 **********************************************************************/

blocks: 
| es = elements;
  ps_opt = option(paragraphs);
  {
   let _ = d_printf ("parser matched: blocks.\n") in
   let es = List.map es ~f:(fun e -> Ast.Block_Element e) in
   let ps = match ps_opt with 
            | None -> []
            | Some ps -> List.map ps ~f:(fun p -> Ast.Block_Paragraph p) 
   in
     es @ ps
  }

/**********************************************************************
 ** END: Blocks
 **********************************************************************/

/**********************************************************************
 ** BEGIN: Elements
 ** An element is a group, a problem cluster, or an atom 
 **********************************************************************/

element:
	a = atom
  {Ast.Element_Atom a}
| g = group
  {Ast.Element_Group g}


elements:
  {[]}
| es = elements;
  e = element; 
  {List.append es [e]}

/*
elements:
	e = element
  {[e]}
| es = elements;
  e = element; 
  {List.append es [e]}
*/

elements_and_tailtext:
  es = atoms; 
  tt = boxes;
  {(es, tt)}			


/**********************************************************************
 ** END: Elements
 **********************************************************************/
			
/**********************************************************************
 ** BEGIN: Parametric Groups
 **********************************************************************/

mk_group_end (kw_e):
  he = kw_e
  {he}

/* There is a shift reduce conflict here but it doesn't matter. Shifting does 
   the right thing. 
*/   
mk_group (kw_b, kw_e):
| preamble = boxes;   
  h_b = kw_b; 
  l = option(label); 
  ats_tt = atoms_and_tailtext; 
  h_e = mk_group_end (kw_e);
  {let (kind, h_bb, pval_opt) = h_b in
   let (pval_f_opt, pval_opt_str) = mk_point_val_f_opt pval_opt in
   let (ats, tt) = ats_tt in
   let (kind_, h_end) = h_e in
   let _ = d_printf ("!parser: group matched with points = %s\n") pval_opt_str in
     Ast.Group (preamble, (kind, h_bb, pval_f_opt, None, l, ats, tt, h_end))
  }

| preamble = boxes; 
  h_b = kw_b;
  t = sq_box; 
  l = option(label); 
  ats_tt = atoms_and_tailtext; 
  h_e = mk_group_end (kw_e);
  {let (kind, h_bb, pval_opt) = h_b in
   let (pval_f_opt, pval_opt_str) = mk_point_val_f_opt pval_opt in
   let (bo, tt, bc) = t in
   let title_part = bo ^ tt ^ bc in
   let h_begin = h_bb ^ title_part in
   let (kind_, h_end) = h_e in
   let (ats, tt) = ats_tt in
   let _ = d_printf ("!parser: group matched with points = %s\n") pval_opt_str in
     Ast.Group (preamble, (kind, h_begin, pval_f_opt, Some tt, l, ats, tt, h_end))
  }

group:
|	x = mk_group(KW_BEGIN_GROUP, KW_END_GROUP)
  { x }
/**********************************************************************
 ** END: Parametric Groups
 **********************************************************************/


/**********************************************************************
 ** BEGIN: Atoms
 **********************************************************************/

atoms:
  {[]}		
| ats = atoms; a = atom
  { List.append ats [a] }

atoms_and_tailtext:
  ats = atoms; 
  tt = boxes;
  {(ats, tt)}			

mk_atom_tail (kw_e):
|  il = option(ilist); 
   h_e = kw_e
  { (il, None, None, None, None, None, h_e) }
| il = option(ilist); 
  s = refsol
  {let (h_b, body, exp_opt, rubric_opt, h_e) = s in
     (il, Some h_b, None, Some body, exp_opt, rubric_opt, h_e)
  }
| il = option(ilist); 
  s = hint
  {let (h_b, body, sol_opt, exp_opt, rubric_opt, h_e) = s in
     (il, Some h_b, Some body, sol_opt, exp_opt, rubric_opt, h_e)
  }


/*  diderot atom */


mk_atom(kw_b, kw_e):
/* atoms with label */
| preamble = boxes;
  h_b = kw_b;
  topt = option (sq_box)
  l = label;
  dopt = option (depend);
  bs = boxes; 
  tail = mk_atom_tail (kw_e)
  {
   let (kind, h_bb, pval_opt) = h_b in
   let (pval_f_opt, pval_opt_str) = mk_point_val_f_opt pval_opt in
   let (il, _, hint, sol, exp, rubric, h_e) = tail in
   let (_, h_end) = h_e in
     match topt with 
     | None -> 
       let h_begin = h_bb in
       let _ = d_printf "\n \n Parsed Atom.1 kind = %s h_begin = %s pval_f_opt = %s " kind h_begin pval_opt_str in
         Atom (preamble, (kind, h_begin, pval_f_opt, None, Some l, dopt, bs, il, hint, sol, exp, rubric, h_end))
     | Some t ->
       let (bo, tt, bc) = t in
       let h_begin = h_bb ^ bo ^ tt ^ bc in   
       let _ = d_printf "\n Parsed Atom.2 kind = %s title = %s pval_f_opt = %s " kind tt pval_opt_str in
         Atom (preamble, (kind, h_begin, pval_f_opt, Some tt, Some l, dopt, bs, il, hint, sol, exp, rubric, h_end))
  }

/* atoms without labels but with depends, may have titles or not */
| preamble = boxes;
  h_b = kw_b;
  topt = option (sq_box);
  d = depend;
  bs = boxes;
  tail = mk_atom_tail (kw_e)
  {
   let (kind, h_bb, pval_opt) = h_b in
   let (pval_f_opt, pval_opt_str) = mk_point_val_f_opt pval_opt in
   let (il, _, hint, sol, exp, rubric, h_e) = tail in
   let (_, h_end) = h_e in
     match topt with 
     | None -> 
       let h_begin = h_bb in
       let _ = d_printf "\n \n Parsed Atom.3 kind = %s h_begin = %s pval_f_opt = %s " kind h_begin pval_opt_str in
         Atom (preamble, (kind, h_begin, pval_f_opt, None, None, Some d, bs, il, hint, sol, exp, rubric, h_end))
     | Some t ->
       let (bo, tt, bc) = t in
       let h_begin = h_bb ^ bo ^ tt ^ bc in   
       let _ = d_printf "\n Parsed Atom.4 kind = %s title = %s pval_f_opt = %s " kind tt pval_opt_str in
         Atom (preamble, (kind, h_begin, pval_f_opt, Some tt, None, Some d, bs, il, hint, sol, exp, rubric, h_end))
  }

/* atoms without labels, without depends, without titles */
| preamble = boxes;
  h_b = kw_b;
  bs = boxes_start_no_sq; 
  tail = mk_atom_tail (kw_e)
  {
   let (kind, h_begin, pval_opt) = h_b in
   let (pval_f_opt, pval_opt_str) = mk_point_val_f_opt pval_opt in
   let (il, _, hint, sol, exp, rubric, h_e) = tail in
   let (_, h_end) = h_e in
     d_printf "\n Parsed Atom.5 kind = %s h_begin = %s pval_f_opt = %s " kind h_begin pval_opt_str;

     Atom (preamble, (kind, h_begin, pval_f_opt, None, None, None, bs, il, hint, sol, exp, rubric, h_end)) 
  }

/* atoms without labels, without depends, with titles */
| preamble = boxes;
  h_b = kw_b;
  t = sq_box; 
  bs = boxes; 
  tail = mk_atom_tail (kw_e)
  {
   let (kind, h_bb, pval_opt) = h_b in
   let (pval_f_opt, pval_opt_str) = mk_point_val_f_opt pval_opt in
   let (il, _, hint, sol, exp, rubric, h_e) = tail in
   let (_, h_end) = h_e in
   let (bo, tt, bc) = t in
   let h_begin = h_bb ^ bo ^ tt ^ bc in   
     d_printf "\n Parsed Atom.6 kind = %s h_begin = %s title = %s pval_f_opt = %s " kind h_begin tt pval_opt_str;
     Atom (preamble, (kind, h_begin, pval_f_opt, Some tt, None, None, bs, il, hint, sol, exp, rubric, h_end))
  }

atom:
|	x = mk_atom(KW_BEGIN_ATOM, KW_END_ATOM)
  { x }


/**********************************************************************
 ** END: Atoms
 **********************************************************************/



