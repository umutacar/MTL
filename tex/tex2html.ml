(**********************************************************************
 ** tex/tex2html.ml
 ** Provides the function mk_translator 
 ** which returns a function that translates tex to html using pandoc.
 **********************************************************************)

open Core
open Utils

(* Turn off all prints *)
let d_printf args = 
    ifprintf stdout args

module Xml = Xml_syntax
module Tex = Tex_syntax

(**********************************************************************
 ** BEGIN: Globals
 **********************************************************************)

type translation_options = bool

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
let body_is_single_par =  false
(* caption can be multiple paragraphs but usually is one *)
let caption_is_single_par =  false 
let choice_is_single_par =  true
let explain_is_single_par =  false
let hint_is_single_par =  false
let refsol_is_single_par =  false
let rubric_is_single_par =  false
let title_is_single_par =  true

let single_paragraph_status_of_kind = 
  [ Xml.body, body_is_single_par;
    Xml.choice, choice_is_single_par;
    Xml.caption, body_is_single_par;
		Xml.explain, explain_is_single_par;
		Xml.hint, hint_is_single_par;
		Xml.refsol, refsol_is_single_par;
		Xml.rubric, rubric_is_single_par;
		Xml.title, title_is_single_par;		
  ]

let get_single_paragraph_status kind = 
   match 
		 List.Assoc.find single_paragraph_status_of_kind 
			 ~equal: String.equal kind 
	 with 
   | Some args -> args
   | None -> (printf "tex2html: FATAL ERROR: unknown kind encountered kind = %s.\n" kind;
              exit Error_code.parse_error_single_paragraph_status_of_unknown_kind)


let target_language_of_kind_is_text = 
  [ Xml.body, false;
    Xml.choice, false;
    Xml.caption, false;
		Xml.explain, false;
		Xml.hint, false;
		Xml.refsol, false;
    Xml.refsol_fillin_question, true;
    Xml.refsol_fillin_answer, false;
		Xml.rubric, false;
		Xml.title, false;
  ]

let is_target_language_text kind = 
   match 
		 List.Assoc.find target_language_of_kind_is_text
			 ~equal: String.equal kind 
	 with 
   | Some args -> args
   | None -> (printf "tex2html: FATAL ERROR: unknown kind encountered kind = %s.\n" kind;
              exit Error_code.parse_error_single_paragraph_status_of_unknown_kind)

(* END: Associative list for single par *)

let latex_document_header = "\\documentclass{article}" 
let latex_diderot_commands = 
"
%% These are set for pandoc compilation.
%% Redefine the commands to make sure that they are what we want.
%% (Override existing definitions)
%%
%% Diderot command: download 
\\renewcommand{\\download}[2]{\\download{#1}{#2}}
%% Diderot command: attach 
\\renewcommand{\\attach}[2]{\\attach{#1}{#2}}
%% Diderot command: infer
\\renewcommand{\infer}[2]{
\\cfrac{#2}{#1}
}
"

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

(* Returns the pandoc command to run by parameterizing 
 * 1) verbosity
 * 2) language parameter.
 * If language "lang" is given then it uses "lang.xml" file
 * for defining the syntax.
 *
 * This file should be in the "kate" directory specified.
 *)
   
let set_pandoc be_verbose meta_dir language = 
  let lang = 
		match language with 
    | None -> ""
    | Some l -> " --syntax-definition=" ^ meta_dir ^ "/" ^ l ^ ".xml"
  in
	let filter = " --lua-filter " ^ meta_dir ^ "/diderot.lua" 
(*
                " --lua-filter " ^ meta_dir ^ "/codeblock.lua" 
               ^ " --lua-filter " ^ meta_dir ^ "/diderotcommands.lua" 
               ^ " --lua-filter " ^ meta_dir ^ "/span.lua" 
*)
               ^ lang in
(*                ^ " --lua-filter " ^ meta_dir ^ "/includevideo.lua" *)

    if be_verbose then
      pandoc_verbose_minor ^ filter
(*
      pandoc_verbose_minor ^ " --lua-filter ./pandoc/filters/codeblock.lua" ^ lang 
*)
    else
      pandoc_minor ^  filter

(* Regular expressions *)
let regexp_html_paragraph = Str.regexp "<p>\\(\\(.\\|\n\\)*\\)</p>\n*"
let regexp_newline = Str.regexp "\n"
let regexp_label = Str.regexp Tex.pattern_label
let regexp_caption = Str.regexp Tex.pattern_caption

(* prep string for conversion *)
let text_prep s = 
  (* Replace NEWLINE with SPACE + NEWLINE
   * This prevents some math conversion problems by making sure that 
   * operators have a space after them in case they had a NEWLINE
   *)
  let s = Str.global_replace regexp_newline " \n" s in

  (* Replace \label{label} declarations with space. 
   * We label things ourselves and don't need them in the xml.
   *)
  (* Don't: labels may appear in verbatim env's.
  let s = Str.global_replace regexp_label " " s in
  *)

	s

(*********************************************************************
 ** END: Globals
 *********************************************************************)

(**********************************************************************
 ** BEGIN: Utils
 **********************************************************************)
(* Create a latex document from contents and preamble *)
let mk_tex_document latex_file_name preamble contents =
	let latex_file = Out_channel.create latex_file_name in
	let () = Out_channel.output_string latex_file (latex_document_header ^ "\n") in
	let () = Out_channel.output_string latex_file (preamble ^ "\n") in
	let () = Out_channel.output_string latex_file (latex_diderot_commands ^ "\n") in
	let () = Out_channel.output_string latex_file (latex_begin_document ^ "\n") in
	let () = Out_channel.output_string latex_file (contents ^ "\n") in
	let () = Out_channel.output_string latex_file (latex_end_document ^ "\n") in
	let () = Out_channel.close latex_file in
	()
(**********************************************************************
 ** END: Utils
 **********************************************************************)



(* Translate the contents of latex_file_name and write it into
 *  html_file_name
 * Ignores all but the first language
 *)
let latex_file_to_html be_verbose meta_dir language_opt (latex_file_name, html_file_name) = 
    (** Beware: pandoc converts everything to unicode
     ** HTML is therefore unicode string.
     ** This matters when printing to terminal which is ASCII
     **)

    let command = (set_pandoc be_verbose meta_dir language_opt) ^ " " ^ latex_file_name ^  " -o " ^ html_file_name  in
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
let md_file_to_html be_verbose meta_dir lang_opt (md_file_name, html_file_name) = 
    (** Beware: pandoc converts everything to unicode
     ** HTML is therefore unicode string.
     ** This matters when printing to terminal which is ASCII
     **)
    let pandoc = set_pandoc be_verbose meta_dir lang_opt in
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

let tex_to_html be_verbose tmp_dir meta_dir default_lang_opt  unique preamble contents match_single_paragraph = 
	let error_out languages = 
		let _ = printf "Parse Error: MTL allows one programming language per atom.\n" in
		let _ = printf "This atom has multiple, i.e., %s" (str_of_str_list languages) in
    let _ = printf "contents = \n%s" contents in
		exit 1
	in
  (* prep for translation *)
  let contents = text_prep contents in
  (* Doing something slightly dangerous.
     Removing "comments" as part of language detection.
     This is not always safe because % can appear inside verbatime environments.
     The hope is that this is not going to cause a huge problem.
   *)
  let languages = dedup_str_list (find_lang (rm_comments contents))  in
  let _ = d_printf "languages found = %s" (str_of_str_list languages) in
	let language_opt = 
		match languages with 
		| [ ] -> default_lang_opt
		| lang::[ ] -> Some lang
		| _ -> error_out languages
	in
  let latex_file_name = tmp_dir ^ "/" ^ unique ^ "." ^ latex_extension in
  let _ = mk_tex_document latex_file_name preamble contents in
  (** translate to html **)
  let html_file_name = tmp_dir ^ "/" ^ unique ^ "." ^ html_extension in
  let () = latex_file_to_html be_verbose meta_dir  language_opt (latex_file_name, html_file_name) in
  let html = In_channel.read_all html_file_name in
	if not match_single_paragraph then
(*      let _ = printf "html: %s" html in *)
    html
  else
    let matched = try Str.search_forward regexp_html_paragraph html 0 
    with Not_found -> -1
    in
        (* Group names start counting from 1. *)
    if matched >= 0 then
      let contents:string = Str.matched_group 1 html  in
(*            printf "matched contents: %s" contents; *)
      contents
    else
      (* Contents was empty.  This is OK. No need to raise an error.
       * let () = printf "\nFATAL ERROR in LaTeX to html translation!\n" in
       * "FATAL ERROR in LaTeX to html translation" 
       *)
      contents


(**********************************************************************)


(**********************************************************************
 ** Translate code contents to html using markdown
 ** tmp_dir is /tmp/ or similar
 ** unique is a unique name that can be used for translation files
 ** contents is the contents to be translated
 **)

let code_to_html be_verbose tmp_dir meta_dir lang_opt unique arg_opt contents = 
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
  let () = md_file_to_html be_verbose meta_dir lang_opt (md_file_name, html_file_name) in
  let html = In_channel.read_all html_file_name in
    html

(**********************************************************************)


(**
 **
 **)
let contents_to_html be_verbose tmp_dir meta_dir lang_opt_default unique preamble contents is_single_paragraph = 
	tex_to_html 
		be_verbose tmp_dir meta_dir lang_opt_default 
		unique preamble contents is_single_paragraph

(**********************************************************************
 ** mk_translator makes a tex to html translator function 
 ** and returns it.  The returned translator function does 
 ** not require a unique string but generates it.
 **********************************************************************)
let mk_translator be_verbose tmp_dir meta_dir  lang_opt (preamble: string) = 
   (* Create tmp dir *) 
   let command = "mkdir " ^ tmp_dir in
   let _ = Sys.command command in  

   (* translator *)
   let translate kind contents = 
     let contents = text_prep contents in 
		 let unique = mk_unique () in
     let options = get_single_paragraph_status kind in
       contents_to_html be_verbose tmp_dir  meta_dir lang_opt unique preamble contents options
   in
     translate


