(**********************************************************************
 ** tex/tex2html.ml
 ** Provides the function mk_translator 
 ** which returns a function that translates tex to html using pandoc.
 **********************************************************************)

open Core

(**********************************************************************
 ** BEGIN: Globals
 **********************************************************************)

type translation_options = Generic of bool | Code of unit 

let html_extension = "html"
let latex_extension = "tex"
let md_extension = "md"


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
let pandoc_minor = "pandoc --verbose --mathjax"
let pandoc =  pandoc_minor


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

(** END: Globals
 **********************************************************************)

(* Translate the contents of latex_file_name and write it into
 *  html_file_name
 *)
let latex_file_to_html (latex_file_name, html_file_name) = 
    (** Beware: pandoc converts everything to unicode
     ** HTML is therefore unicode string.
     ** This matters when printing to terminal which is ASCII
     **)
    let command = pandoc ^ " " ^ latex_file_name ^  " -o" ^ html_file_name  in
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


(* Translate the contents of wd_file_name and write it into
 *  html_file_name
 *)
let md_file_to_html (md_file_name, html_file_name) = 
    (** Beware: pandoc converts everything to unicode
     ** HTML is therefore unicode string.
     ** This matters when printing to terminal which is ASCII
     **)
    let command = pandoc ^ " " ^ md_file_name ^  " -o" ^ html_file_name  in
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

let tex_to_html tmp_dir  unique preamble contents match_single_paragraph = 
  (* prep for translation *)
  let contents = text_prep contents in
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
  let () = latex_file_to_html (latex_file_name, html_file_name) in
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

let code_to_html tmp_dir  unique contents = 
  (* prep for translation *)
  let md_file_name = tmp_dir ^ "/" ^ unique ^ "." ^ md_extension in
  let md_file = Out_channel.create md_file_name in

  (* TODO: update this *)
  let heading = "~~~~{.c .numberLines startFrom=\"100\"}" in
  let ending = "~~~~" in
  let () = Out_channel.output_string md_file (heading ^ "\n") in
  let () = Out_channel.output_string md_file (contents ^ "\n") in
  let () = Out_channel.output_string md_file (ending ^ "\n") in
  let () = Out_channel.close md_file in

  (** translate to html **)
  let html_file_name = tmp_dir ^ "/" ^ unique ^ "." ^ html_extension in
  let () = md_file_to_html (md_file_name, html_file_name) in
  let html = In_channel.read_all html_file_name in
    html

(**********************************************************************)


(**
 **
 **)
let contents_to_html tmp_dir  unique preamble contents options = 
  match options with 
  | Generic is_single_paragraph -> tex_to_html tmp_dir unique preamble contents is_single_paragraph
  | Code _ -> code_to_html tmp_dir unique contents 


(**********************************************************************
 ** mk_translator makes a tex to html translator function 
 ** and returns it
 **********************************************************************)
let mk_translator (tmp_dir, preamble) = 
   (* Create tmp dir *) 
   let command = "mkdir " ^ tmp_dir in
   let _ = Sys.command command in  
   (* translator *)
   let translate unique contents match_single_paragraph = 
     let contents = text_prep contents in 
       tex_to_html tmp_dir unique preamble contents match_single_paragraph
   in
     translate


