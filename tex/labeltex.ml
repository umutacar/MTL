open Core
open Lexer
open Lexing

(* Stub. *)
let handle_parser_error () = 
  printf ("Parse Error\n.")

let tex2ast infile = 
	let ic = In_channel.create infile in
   	try 
      let lexbuf = Lexing.from_channel ic in
	    let ast_chapter = Parser.chapter Lexer.token lexbuf in
        ast_chapter
    with | End_of_file -> exit 0
         | Parser.Error as exn -> 
           handle_parser_error (); 
           raise exn

let tex2ast infile = 
	let ic = In_channel.create infile in
   	try 
      let lexbuf = Lexing.from_channel ic in
	    let ast_chapter = Parser.chapter Lexer.token lexbuf in
        ast_chapter
    with End_of_file -> exit 0


let ast2tex ast_chapter = 
  Ast.chapterToTex ast_chapter

let labeltex infile = 
  let infile_inlined = Preprocessor.inline_file infile in
  (* Make AST *)
  let ast = tex2ast infile_inlined in

  (* Label AST *)
  let ast_labeled = Ast.labelChapter ast in

  (* Make TeX *)
  let result = ast2tex ast_labeled in
    result

let main () =
	let args = Sys.argv in
    if Array.length args = 2 then
      let infile = args.(1) in
      let result = labeltex infile in
        printf "Successfully labeled, result =  %s\n" result 
      else if Array.length args = 3 then    
        let infile = args.(1) in
        let outfile = args.(2) in
        let result = labeltex infile in
        let _ = Out_channel.write_all outfile ~data:result in
        let _ = printf "Successfully labeled. Output in %s\n" outfile in
           ()
      else
         printf "Usage: main <input latex file> [<output latex file>]\n" ;;
					
let _ = main ()
