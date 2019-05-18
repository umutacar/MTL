open Core
open Lexer
open Lexing

let default_tmp_dir = "/tmp"

let mk_translator preamble_filename = 
  let preamble = In_channel.read_all preamble_filename in
    Tex2html.mk_translator default_tmp_dir None preamble 

let tex2ast infile = 
	let ic = In_channel.create infile in
   	try 
      let lexbuf = Lexing.from_channel ic in
	    let ast_chapter = Parser.chapter Lexer.token lexbuf in
        ast_chapter
    with End_of_file -> exit 0

let ast2xml ast_chapter preamble_filename = 
  (* Elaborate AST *)
  let ast_elaborated = Ast.chapterEl ast_chapter in
  (* Make XML *)
  let tex2html = mk_translator preamble_filename in
  let chapter_xml = Ast.chapterToXml tex2html ast_elaborated in
    printf "Parsed successfully chapter.\n";
    chapter_xml

let tex2xml do_inline infile preamble_filename = 
  (* Preprocess *)
  let infile_inlined = 
        if do_inline then
          Preprocessor.inline_file infile
        else 
          infile
  in
  (* Make AST *)
	let ast_chapter = tex2ast infile_inlined in

  (* Translate to XML *)
  let xml_chapter = ast2xml ast_chapter preamble_filename in
    xml_chapter

let main () =
	let args = Sys.argv in
    if Array.length args == 4 then
      let infile = Sys.argv.(1) in
      let preamble_filename = Sys.argv.(2) in
      let outfile = Sys.argv.(3) in
      let do_inline = true in
      let xml_chapter = tex2xml do_inline infile preamble_filename in      
         Out_channel.write_all outfile ~data:xml_chapter 
    else if Array.length args == 5 then
      let infile = Sys.argv.(1) in
      let preamble_filename = Sys.argv.(2) in
      let outfile = Sys.argv.(3) in
      let do_inline = bool_of_string (Sys.argv.(4)) in
      let xml_chapter = tex2xml do_inline infile preamble_filename in      
         Out_channel.write_all outfile ~data:xml_chapter 
    else
      printf "Usage: main  <input latex file> <input preamble file> <output xml file> [inline = *true/false]\n";;			
					
let _ = main ()

