type preamble = string
type atom_kind = string
type atom_body = string
type title = string
type keyword = string

(* Keywords are used to capture the "beginning" and "end" of the commands.
   For example, "    \label   {"  and "}    \n", 
                "\begin{example}  \n"
                "\end{example}  \n\n\n"
                  

   Because we don't care about white space, they might have whitespace in them.
 *)

type label = Label of keyword * string * keyword 
type atom = Atom of preamble * (atom_kind * title option * label option * keyword * atom_body * keyword) 

type group = 
  Group of preamble 
           * (title option * label option * keyword * atom list * keyword) 
           * postamble

type chapter = 
  Chapter of (title * label * keyword * block list * section list) 
             * postamble

and section = 
  Section of (title * label option * keyword * block list * subsection list)
             * postamble
and subsection = 
  Subsection of (title * label option * keyword * block list * subsubsection list)
                * postamble

and subsubsection = 
  Subsubsection of (title * label option * keyword * block list * paragraph list)
                   * postamble

and paragraph = 
  Paragraph of (title * label option * keyword * block list)
               * postamble
and block = 
  | Block_Group of group
  | Block_Atom of atom

let map_concat f xs = 
  let xs_s = List.map f xs in
  let result = List.fold_left (fun result x -> result ^ x) "" xs_s in
    result

(**********************************************************************
 ** BEGIN: AST To String
*********************************************************************)
let labelToString (Label(hb, label_string, he)) = 
  hb ^  label_string ^ he

let labelOptionToString lo = 
  let r = match lo with 
              |  None -> ""
              |  Some l -> labelToString l  in
     r

let titleOptionToString topt = 
  let r = match topt with 
              |  None -> ""
              |  Some s -> s in
     r

let atomToString (Atom(preamble, (kind, topt, lo, hb, ab, he))) = 
  let label = "label: " ^ labelOptionToString lo in
  let heading =  match topt with
                 | None -> "Atom:" ^ hb 
                 | Some t -> "Atom:" ^ hb ^ "[" ^ t ^ "]" 
  in
    preamble ^ heading ^ label ^ ab ^ he

let groupToString (Group(preamble, (topt, lo, hb, ats, he), postamble)) = 
  let atoms = map_concat atomToString ats in
  let label = "label: " ^ labelOptionToString lo in
  let heading = match topt with
                | None -> hb
                | Some t -> hb ^ "title:" ^ t in
    preamble ^ 
    heading ^ label ^ atoms ^ he ^ 
    postamble

let blockToString b = 
  match b with
  | Block_Group g -> groupToString g
  | Block_Atom a -> atomToString a

let paragraphToString (Paragraph (preamble, (t, lo, h, bs), postamble)) =
  let blocks = map_concat blockToString bs in
  let title = "title: " ^ t in
  let label = "label: " ^ labelOptionToString lo in
    "*paragraph:" ^ title ^ label ^ h ^ blocks ^ 
    postamble

let subsubsectionToString (Subsubsection (preamble, (t, lo, h, bs, ss), postamble)) =
  let blocks = map_concat blockToString bs in
  let nesteds = map_concat paragraphToString ss in
  let title = "title: " ^ t in
  let label = "label: " ^ labelOptionToString lo in
    "*subsubsection:" ^ title ^ label ^ h ^ blocks ^ nesteds ^ 
    postamble

let subSectionToString (Subsection (preamble, (t, lo, h, bs, ss))) =
  let blocks = map_concat blockToString bs in
  let nesteds = map_concat subsubsectionToString ss in
  let title = "title: " ^ t in
  let label = "label: " ^ labelOptionToString lo in
   "*subsection:" ^ title ^ label ^ h ^ blocks ^ nesteds ^
   postamble

let sectionToString (Section (preamble, (t, lo, h, bs, ss))) =
  let blocks = map_concat blockToString bs in
  let nesteds = map_concat subSectionToString ss in
  let title = "title: " ^ t in
  let label = "label: " ^ labelOptionToString lo in
    "*section:" ^ title ^ label ^ h ^ blocks ^ nesteds ^
    postamble

let chapterToString (Chapter (t, l, h, bs, ss)) =
  let blocks = map_concat blockToString bs in
  let sections = map_concat sectionToString ss in
  let title = "title: " ^ t in
  let label = labelToString l in
    "*chapter:" ^ title ^ label ^ h ^ blocks ^ sections ^
    postamble

(**********************************************************************
 ** END: AST To String
 **********************************************************************)

(**********************************************************************
 ** BEGIN: AST To LaTeX
 **********************************************************************)
let atomToTex (Atom(preamble, (kind, topt, lo, hb, ab, he))) = 
  let label = labelOptionToString lo in
  let heading =  match topt with
                 | None -> "Atom:" ^ hb 
                 | Some t -> "Atom:" ^ hb ^ "[" ^ t ^ "]" 
  in
    preamble ^ heading ^ label ^ ab ^ he
      

let groupToTex (Group(preamble, (topt, lo, hb, ats, he), postamble)) = 
  let atoms = map_concat atomToTex ats in
  let label = labelOptionToString lo in
  let heading = match topt with
                | None -> hb
                | Some t -> hb ^ t in
    preamble ^
    heading ^ label ^ atoms ^ he ^ 
    postamble

let blockToTex b = 
  match b with
  | Block_Group g -> groupToTex g
  | Block_Atom a -> atomToTex a


let paragraphToTex (Paragraph ((t, lo, h, bs), postamble)) =
  let blocks = map_concat blockToTex bs in
  let label = labelOptionToString lo in
    h ^ label ^ blocks ^ postamble

let subsubsectionToTex (Subsubsection ((t, lo, h, bs, ss), postamble)) =
  let blocks = map_concat blockToTex bs in
  let nesteds = map_concat paragraphToTex ss in
  let label = labelOptionToString lo in
    h ^ label ^ blocks ^ nesteds ^ postamble

let subsectionToTex (Subsection ((t, lo, h, bs, ss), postamble)) =
  let blocks = map_concat blockToTex bs in
  let nesteds = map_concat subsubsectionToTex ss in
  let label = labelOptionToString lo in
    h ^ label ^ blocks ^ nesteds ^ postamble

let sectionToTex (Section ((t, lo, h, bs, ss), postamble)) =
  let blocks = map_concat blockToTex bs in
  let nesteds = map_concat subsectionToTex ss in
  let label = labelOptionToString lo in
    h ^ label ^ blocks ^ nesteds ^ postamble

let chapterToTex (Chapter ((t, l, h, bs, ss), postamble)) =
  let blocks = map_concat blockToTex bs in
  let sections = map_concat sectionToTex ss in
  let label = labelToString l in
    h ^ label ^ blocks ^ sections ^ postamble

(**********************************************************************
 ** END: AST To LaTeX
 **********************************************************************)




