(**********************************************************************
 ** tex/tex2html.ml
 ** Provides the function mk_translator 
 ** which returns a function that translates tex to html using pandoc.
 **********************************************************************)

open Core
open Utils

module Xml = Xml_syntax

(**********************************************************************
 ** BEGIN: Globals
 **********************************************************************)

type translation_options = 
  Generic of bool 
| Code of string option * string option (* code is language name and other argument *) 

let html_extension = "html"
let latex_extension = "tex"
let md_extension = "md"

(* A simple counter based unique number generation *)
let unique = ref 0
let mk_unique () = 
  let r = string_of_int !unique in
  let _ = unique := !unique + 1 in
    r
(* BEGIN: Associative list for single par *)

(* *_single_par flags are used for html post-processing:
 *  "true" means that this was a single paragraph and the
 * <p> </p> annotations must be removed.
 *) 
let body_is_single_par = Tex2html.Generic false
let explain_is_single_par = Tex2html.Generic false
let hint_is_single_par = Tex2html.Generic false
let refsol_is_single_par = Tex2html.Generic false
let rubric_is_single_par = Tex2html.Generic false
let title_is_single_par = Tex2html.Generic true
let atom_is_code lang_opt arg_opt = Tex2html.Code (lang_opt, arg_opt)

let single_paragraph_status_of_kind = 
  [ Xml.body, body_is_single_par;
		Xml.explain, explain_is_single_par;
		Xml.hint, hint_is_single_par;
		Xml.refsol, refsol_is_single_par;
		Xml.rubric, rubric_is_single_par;
		Xml.title, title_is_single_par;		
  ]

let mk_single_paragraph_status kind = 
   match 
		 List.Assoc.find single_paragraph_status_of_kind 
			 ~equal: String.equal kind 
	 with 
   | Some args -> args
   | None -> (printf "FATAL ERROR: unknown kind encountered kind = %s.\n" kind;
              exit ErrorCode.single_paragraph_status_error_unknown_atom)

(* END: Associative list for single par *)

let latex_document_header = "\\documentclass{article}" 
let latex_begin_document = "\\begin{document}"
let latex_end_document = "\\end{document}"

(** generate standalone html files
 **
 ** Can use Mathml or mathjax but 
 ** mathml is not supported natively by many browsers
 **)

(* pandoc_standalone = "pandoc --mathml -s" *)
(* let pandoc_standalone = "pandoc --from latex+smart  --mathjax -s" *)
let pandoc_standalone = "pandoc  --mathjax -s"

(* generate non-standalone html files *)
(* let pandoc_minor = "pandoc --from latex+smart  --mathjax" *)
let pandoc_minor = "pandoc --mathjax"
let pandoc_verbose_minor = "pandoc --verbose --mathjax"
let pandoc =  pandoc_minor

(* Returns "./kate/language.xml" *)
let mk_kate_language l = "./kate/" ^ l ^ ".xml"

let set_pandoc be_verbose language = 
  let lang = match language with 
             | None -> ""
             | Some l -> " --syntax-definition=" ^ (mk_kate_language l)
  in
    if be_verbose then
      pandoc_verbose_minor ^ " --lua-filter ./pandoc/filters/codeblock.lua" ^ lang 
    else
      pandoc_minor ^  " --lua-filter ./pandoc/filters/codeblock.lua" ^ lang


(* Regular expressions *)
let pattern_html_paragraph = Str.regexp "<p>\\(\\(.\\|\n\\)*\\)</p>\n*"
let pattern_newline = Str.regexp "\n"

(* prep string for conversion *)
let text_prep(s) = 
  (* Replace NEWLINE with SPACE + NEWLINE
   * This prevents some math conversion problems by making sure that 
   * operators have a space after them in case they had a NEWLINE
   *)
  Str.global_replace pattern_newline " \n" s

(*********************************************************************
 ** END: Globals
 *********************************************************************)

(**********************************************************************
 ** BEGIN: Utils
 **********************************************************************)

(* Return the list of languages used in the contents 
   TODO: this looks into comments
 *)
let findLang contents  =
  let extract_lang (m: Re2.Match.t) =
    let source = Re2.Match.get ~sub:(`Name "lang") m in
      match source with 
      | None -> let _ = d_printf "tex2html.findLang: None" in []
      | Some x -> let _ = d_printf "tex2html.findLang: Some %s" x in [x]
  in
  (* The quad escape's are due to ocaml's string representation that requires escaping \ *)
  let regex = Re2.create_exn
                  "\\\\begin{lstlisting}\\[language[' ']*=[' ']*(?P<lang>[[:alnum:]]*)([','' ''=']|[[:alnum:]])*\\]"    
  in
  let pattern = Re2.pattern regex in
  let _ = printf "tex2html.findLang: Pattern for this regex = %s\n" pattern in 

  let all_matches = Re2.get_matches_exn regex contents in
  let languages: string list = List.concat_map all_matches ~f:extract_lang in
  let _ = printf_strlist "tex2html.findLange: languages" languages in 
    languages

(**********************************************************************
 ** END: Utils
 **********************************************************************)



(* Translate the contents of latex_file_name and write it into
 *  html_file_name
 * Ignores all but the first language
 *)
let latex_file_to_html be_verbose languages (latex_file_name, html_file_name) = 
    (** Beware: pandoc converts everything to unicode
     ** HTML is therefore unicode string.
     ** This matters when printing to terminal which is ASCII
     **)

    let language = 
       match languages with 
       | [] -> None
       | h::t -> Some h
    in
    let command = (set_pandoc be_verbose language) ^ " " ^ latex_file_name ^  " -o " ^ html_file_name  in
    let _ = printf "\n*latex_file_to_html: Executing command: %s\n" command in
    let exit_code = Sys.command command in 
      if exit_code <> 0 then
        begin
          printf "Error in html translation.\n";
          printf "Command exited with code: %d\n" exit_code;
          printf "Now exiting.";
          exit exit_code
        end
      else
        begin
          printf "LaTex code is in file: %s\n" latex_file_name;
          printf "HTML code is in file: %s\n" html_file_name
        end


(* Translate the contents of md_file_name and write it into
 *  html_file_name
 *)
let md_file_to_html be_verbose lang_opt (md_file_name, html_file_name) = 
    (** Beware: pandoc converts everything to unicode
     ** HTML is therefore unicode string.
     ** This matters when printing to terminal which is ASCII
     **)
    let pandoc = set_pandoc be_verbose lang_opt in
    let command = pandoc ^ " " ^ md_file_name ^  " -o " ^ html_file_name in
    let _ = printf "\n*md_file_to_html: Executing command: %s\n" command in
    let exit_code = Sys.command command in 
      if exit_code <> 0 then
        begin
          printf "Error in html translation.\n";
          printf "Command exited with code: %d\n" exit_code;
          printf "Now exiting.";
          exit exit_code
        end
      else
        begin
          printf "Markdown code is in file: %s\n" md_file_name;
          printf "HTML code is in file: %s\n" html_file_name
        end

(**********************************************************************
 ** Translate latex (contents) to html
 ** tmp_dir is /tmp/ or similar
 ** unique is a unique name that can be used for translation files
 ** preamble is the preamble file
 ** contents is the contents to be translated
 ** match specifies that what is expected is a single paragraph
 **)

let tex_to_html be_verbose default_lang tmp_dir  unique preamble contents match_single_paragraph = 
  (* prep for translation *)
  let contents = text_prep contents in
  let languages = findLang contents  in
  let languages = match languages with 
                  | [] -> (match default_lang with 
                           | None -> []
                           | Some x -> [x])
                  | _ -> languages
  in       
  let latex_file_name = tmp_dir ^ "/" ^ unique ^ "." ^ latex_extension in
  let latex_file = Out_channel.create latex_file_name in
  let () = Out_channel.output_string latex_file (latex_document_header ^ "\n") in
  let () = Out_channel.output_string latex_file (preamble ^ "\n") in
  let () = Out_channel.output_string latex_file (latex_begin_document ^ "\n") in
  let () = Out_channel.output_string latex_file (contents ^ "\n") in
  let () = Out_channel.output_string latex_file (latex_end_document ^ "\n") in
  let () = Out_channel.close latex_file in

  (** translate to html **)
  let html_file_name = tmp_dir ^ "/" ^ unique ^ "." ^ html_extension in
  let () = latex_file_to_html be_verbose languages (latex_file_name, html_file_name) in
  let html = In_channel.read_all html_file_name in
    if not match_single_paragraph then
(*      let _ = printf "html: %s" html in *)
        html
    else
      let matched = try Str.search_forward pattern_html_paragraph html 0 
                    with Not_found -> -1
      in
        (* Group names start counting from 1. *)
        if matched >= 0 then
          let contents:string = Str.matched_group 1 html  in
(*            printf "matched contents: %s" contents; *)
            contents
        else
          let () = printf "\nFATAL ERROR in LaTeX to html translation!\n" in
            "FATAL ERROR in LaTeX to html translation"

(**********************************************************************)


(**********************************************************************
 ** Translate code contents to html using markdown
 ** tmp_dir is /tmp/ or similar
 ** unique is a unique name that can be used for translation files
 ** contents is the contents to be translated
 **)

let code_to_html be_verbose tmp_dir lang_opt unique arg_opt contents = 
  (* prep for translation *)
  let md_file_name = tmp_dir ^ "/" ^ unique ^ "." ^ md_extension in
  let md_file = Out_channel.create md_file_name in

  let arg = match arg_opt with 
            | None -> ""
            | Some x -> x
  in
  let _ = printf "code_to_html: arg = %s\n" arg in
  let heading = "~~~~{ " ^ arg ^ " }" in
  let ending = "~~~~" in
  let () = Out_channel.output_string md_file (heading ^ "\n") in
  let () = Out_channel.output_string md_file (contents ^ "\n") in
  let () = Out_channel.output_string md_file (ending ^ "\n") in
  let () = Out_channel.close md_file in

  (** translate to html **)
  let html_file_name = tmp_dir ^ "/" ^ unique ^ "." ^ html_extension in
  let () = md_file_to_html be_verbose lang_opt (md_file_name, html_file_name) in
  let html = In_channel.read_all html_file_name in
    html

(**********************************************************************)


(**
 **
 **)
let contents_to_html be_verbose tmp_dir lang_opt_default unique preamble contents options = 
  match options with 
  | Generic is_single_paragraph -> tex_to_html be_verbose lang_opt_default tmp_dir unique preamble contents is_single_paragraph
  | Code (lang_opt, arg_opt) -> 
    match lang_opt with 
    | None -> 
      (match lang_opt_default with 
       | None -> code_to_html be_verbose tmp_dir None unique arg_opt contents
       | Some lang -> let lang_arg = MdSyntax.mk_code_block_arg_indicate lang in
                      let arg_opt_new = MdSyntax.add_to_code_block_arg lang_arg arg_opt in 
                        code_to_html be_verbose tmp_dir lang_opt_default unique arg_opt_new contents 
      )
    | Some lang -> code_to_html be_verbose tmp_dir (Some lang) unique arg_opt contents


(**********************************************************************
 ** mk_translator makes a tex to html translator function 
 ** and returns it.  The returned translator requires
 ** a unique string.
 **********************************************************************)
let mk_translator be_verbose tmp_dir lang_opt preamble = 
   (* Create tmp dir *) 
   let command = "mkdir " ^ tmp_dir in
   let _ = Sys.command command in  

   (* translator *)
   let translate unique contents options = 
     let contents = text_prep contents in 
       contents_to_html be_verbose tmp_dir lang_opt unique preamble contents options
   in
     translate

(**********************************************************************
 ** mk_translator makes a tex to html translator function 
 ** and returns it.  The returned translator function does 
 ** not require a unique string but generates it.
 **********************************************************************)
let mk_translator_auto be_verbose tmp_dir lang_opt preamble = 
   (* Create tmp dir *) 
   let command = "mkdir " ^ tmp_dir in
   let _ = Sys.command command in  

   (* translator *)
   let translate contents options = 
     let contents = text_prep contents in 
		 let unique = mk_unique () in
       contents_to_html be_verbose tmp_dir lang_opt unique preamble contents options
   in
     translate

