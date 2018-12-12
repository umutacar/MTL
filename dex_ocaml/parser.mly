%{
open Core
open Printf
open Atoms

let parse_error s = printf "Parse Error: %s"
%}	


%token EOF

%token <string> ATOM
%token <string> WORD


%token <string> BACKSLASH
%token <string> O_CURLY C_CURLY	
%token <string> O_SQ_BRACKET C_SQ_BRACKET

	
%token <string> HEADING_CHAPTER
%token <string> HEADING_SECTION
%token <string> HEADING_SUBSECTION
%token <string> HEADING_SUBSUBSECTION	
%token <string> HEADING_PARAGRAPH	
%token <string> HEADING_SUBPARAGRAPH

%token KW_BEGIN KW_END

%token <string> ENV_B_GROUP ENV_E_GROUP
%token <string> ENV_B_DEFINITION ENV_E_DEFINITION
%token <string> ENV_B_EXAMPLE ENV_E_EXAMPLE
	
%start chapter
%type <Ast.chapter> chapter
%type <Ast.section> section
%type <Ast.section List.t> sections
%type <Ast.group> group
%type <Ast.atom> atom

%%

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
| b = BACKSLASH w = WORD
  {b ^ w}


/* a box is the basic unit of composition */
box:
  w = word 
  {w}
| b = curly_box 
  {let (bo, bb, bc) = b in bo ^ bb ^ bc}
| b = sq_box 
  {let (bo, bb, bc) = b in bo ^ bb ^ bc}


boxes:
  {""}
| bs = boxes; b = box
  {bs ^ b }


/* This is a sequence of boxes where the first box must not be square. */
boxes_start_no_sq:
  {""}
|	w = word; bs = boxes
  {w ^ bs}
|	b = curly_box; bs = boxes
  {let (bo, bb, bc) = b in bo ^ bb ^ bc ^ bs }


chapter_heading:
  hc = HEADING_CHAPTER; b = curly_box 
  {let (bo, bb, bc) = b in (hc ^ bo ^ bb ^ bc, bb) }


section_heading:
  hs = HEADING_SECTION; b = curly_box 
  {let (bo, bb, bc) = b in (hs ^ bo ^ bb ^ bc, bb) }


env_begin:
  KW_BEGIN; co = O_CURLY; a = ATOM; cc = C_CURLY 
  {("\\begin" ^ co ^ a ^ cc, a)}

env_begin_sq:
  KW_BEGIN; co = O_CURLY; a = ATOM; cc = C_CURLY; b =  sq_box 
  {let (bo, bb, bc) = b in 
   let hb = "\\begin" ^ co ^ a ^ cc in
     (hb ^  bo ^ bb ^ bc, a, bb)
  }

env_end:
  KW_END; co = O_CURLY; a = ATOM; cc = C_CURLY 
  {"\\end" ^ co ^ a ^ cc}


env_b_group:
  hb = ENV_B_GROUP
  {hb}


env_b_group_sq:
  hb = ENV_B_GROUP; b = sq_box
  {let (bo, bb, bc) = b in (hb ^ bo ^ bb ^ bc, bb)}


env_e_group:
  he = ENV_E_GROUP
  {he}

chapter:
  h = chapter_heading; bs = blocks; ss = sections; EOF 
  {let (hc, t) = h in Ast.Chapter(t, hc, bs, ss)}
|	h =  chapter_heading; ss = sections; EOF
  {let (hc, t) = h in Ast.Chapter (t, hc, [], ss)}		

section: 
  h = section_heading; bs = blocks
  {let (hc, t) = h in Ast.Section(t, hc, bs)}		
	
sections:
| s = section; {[s]}
| ss = sections; s = section
  {List.append ss [s]}


blocks:
	b = block 
  {[b]}
| bs = blocks; b = block
  {List.append bs [b]}


block:
	a = atom
  {Ast.Block_Atom a}
| g = group
  {Ast.Block_Group g}

			
group:
  hb = env_b_group; ats = atoms; he = env_e_group
  {Ast.Group (None, hb, ats, he)}
| hb = env_b_group_sq; ats = atoms; he = env_e_group
  {let (hb, t) = hb in Ast.Group (Some t, hb, ats, he)}

atoms:
  {[]}		
| ats = atoms; a = atom
  { List.append ats [a] }

	
atom:
| hbk = env_begin; bs = boxes_start_no_sq; he = env_end
  {let (hb, kind) = hbk in
     Atom (kind, None, hb, bs, he) 
  }
| hbkt = env_begin_sq; bs = boxes; he = env_end
  {let (hb, kind, title) = hbkt in
     Atom (kind, Some title, hb, bs, he) 
  }



/*
|	hb = env_b_definition; bs = boxes_start_no_sq; he = env_e_definition
  { Atom (atom_definition, None, hb, bs, he) }
|	hb = env_b_definition_sq; bs = boxes; he = env_e_definition
  {let (hb, t) = hb in Atom (atom_definition, Some t, hb, bs, he) }
| hb = env_b_example; bs = boxes_start_no_sq;  he = env_e_example
  { Atom (atom_example, None, hb, bs, he) }
| hb = env_b_example_sq; bs = boxes; he = env_e_example
  { let (hb, t) = hb in Atom (atom_example, Some t, hb, bs, he) }
*/