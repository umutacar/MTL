(* md/mdxml.ml
 * Translate markdown to xml
 *)
open Core
open Lexing

module Ast = Ast
module Lexer = Md_lexer
module Parser = Md_parser
module Translator = Md2html

let file_extension_xml = ".xml"
let verbose = ref false
let do_inline = ref false
(* Specify type, so inference can proceed *)
let default_lang: string option ref = ref None
let meta_dir = ref "."  (* Current directory by default *)
let tmp_dir = ref "/tmp"
let bib_file = ref None
let preamble_file = ref None
let in_file = ref None
let out_file = ref None


(* Set string argument *)
let set_str_arg r v = r := Some v

(* Get value of string argument *)
let get_str_arg r v =
  match !r with 
  | None -> (printf "Fatal Error"; exit 1)
  | Some s -> s

let mk_translator () = 
  let preamble = 
    match !preamble_file with 
    | None -> ""
    | Some x -> In_channel.read_all x
  in
    Translator.mk_translator 
		!verbose 
		!tmp_dir 
		!meta_dir
		!default_lang
		preamble 

let md2ast infile = 
(*	let ic = In_channel.create infile in *)
  let contents = In_channel.read_all infile in
  let tripledash = Str.regexp "---" in
  let contents = 
    if Str.string_match tripledash contents 0 then
      try 
        let pos = Str.search_forward tripledash contents 3 in
				  String.slice contents (pos + 3) (String.length contents)
       with Not_found -> contents
    else
			contents
  in
(*
  let _ = printf "**contents:\n%s" contents in 
  let _ = printf "**contents done\n" in 
*)
	let ast = 
   	try 
(*      let lexbuf = Lexing.from_channel ic in *)
      let lexbuf = Lexing.from_string contents in
	    let ast = Parser.top Lexer.lexer lexbuf in
			match ast with 
			| None -> (printf "Parse Error."; exit 1)
			| Some ast -> ast
    with End_of_file -> exit 0
	in
	let _ = Ast.validate ast in
		ast


let ast2xml be_verbose lang_opt ast preamble_file = 
  (* Normalize AST *)
  let _  = Ast.normalize ast in

  (* Assign labels *)
  let _ = Ast.assign_labels ast in

  (* Make XML *)
  let md2html = mk_translator () in
  let xml = Ast.to_xml md2html ast in
    printf "Parsed successfully chapter.\n";
    xml

let md2xml be_verbose do_inline infile preamble_file lang_opt = 
  (* Preprocess *)
  let infile_inlined = 
        if do_inline then
          Preprocessor.inline_file infile
        else 
          infile
  in
  (* Make AST *)
	let ast_chapter = md2ast infile_inlined in

  (* Translate to XML *)
  let xml_chapter = ast2xml be_verbose lang_opt ast_chapter preamble_file in
    xml_chapter

					
let main () = 
  let spec = [
              ("-v", Arg.Set verbose, "Enables verbose mode; default is false.");
(*              ("-inline", Arg.Set do_inline, "Inline latex input directives; default is false."); *)
              ("-o", Arg.String (set_str_arg out_file), "Sets output file");
              ("-bib", Arg.String (set_str_arg bib_file), "Sets bibliography (bib) file if any.");
              ("-meta", Arg.Set_string meta_dir, "Directory for meta informaiton, e.g., highlighting definitions, lua filters, etc.");
              ("-tmp", Arg.Set_string tmp_dir, "Sets the temporary directory, default is /tmp.")
(*  Don't support default language, preamble.
              ("-lang", Arg.String (set_str_arg default_lang), "Sets the default programming language.");

              ("-preamble", Arg.String (set_str_arg preamble_file), "Sets LaTeX preamble, if any.");
*)
             ]
  in 

  let take_infile_name anon = 
    match !in_file with 
    | None -> in_file := Some anon
    | Some _ -> (printf "Warning: multiple input files specified, taking first.\n")
  in

  let usage_msg = "mdxml translates latex to XML. \n Usage: mdxml <latex file>.\n Options available:" 
  in
  let _  = Arg.parse spec take_infile_name usage_msg in
  let in_file_name =  
    match !in_file with 
    | None -> (printf "Error: Missing input Latex file! \n%s" (Arg.usage_string spec usage_msg); exit 1)
    | Some x -> x
  in
  let _ = printf "Executing command: mdxml %s\n" in_file_name in
  let outfile_name = match !out_file with 
          | None -> 
            let x = Utils.mk_xml_filename in_file_name in
              (out_file := Some x; x)
          | Some x -> x
  in
  let xml_chapter = md2xml !verbose !do_inline in_file_name !preamble_file !default_lang in       
  let _ = Out_channel.write_all outfile_name ~data:xml_chapter in
     printf "Output written in %s\n" outfile_name 
		
  

let _ = main ()

