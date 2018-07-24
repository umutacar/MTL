######################################################################
## dex/parser.py
######################################################################

import os
import re
import sys
from functools import partial as curry

import pyparsing as pp 

from pervasives.parser import *
from pervasives.syntax import *

import syntax as dex
#import dex.pretty_print as dexpp
import blocks as blocks
import tokens as tokens

######################################################################
## BEGIN Globals


# Translate a simple answer to an answer
def simple_answer_to_answer(toks):
#  print 'simple_ans_to_answer:', toks
  # ans is a list o point (optional) and  body string
  ans = tokens.get_ans(toks)
#  print 'ans:', ans
  explain = tokens.get_explain(toks)
#  print 'explain:', explain
  # points is optional
  points = tokens.get_points_opt(ans)
#  print 'simple_ans_to_answer: points = ', points
  body = tokens.get_body(ans)
  block = blocks.Answer({tokens.KEY_POINTS:points, \
                           tokens.KEY_BODY:body, \
                           tokens.KEY_EXPLAIN:explain})
  return block.to_string()

# Translate a simple choice to choice
def simple_choice_to_choice(toks):
#  print 'simple_choice_to_choice:', toks
  # choice is a list of point (optional) and  body string
  choice = tokens.get_choi(toks)
#  print 'choice:', choice

  explain = tokens.get_explain(toks)
#  print 'explain:', explain
  # points is optional

  points = tokens.get_points_opt(choice)
#  print 'simple_choice_to_answer: points = ', points
  body = tokens.get_body(choice)
  block = blocks.Choice({tokens.KEY_POINTS:[points], \
                           tokens.KEY_BODY:body, \
                           tokens.KEY_EXPLAIN:explain})
  return block.to_string()

# Translate a simple choice_s (star choice) to choice
def simple_choice_s_to_choice(toks):
#  print 'simple_choice_s_to_choice:', toks
  # choice is a  body string
  choice = tokens.get_choi(toks)
#  print 'choice:', choice

  explain = tokens.get_explain(toks)
#  print 'explain:', explain
  # points is optional

  ## Figure points
  points = tokens.get_points_opt(choice)
  if points == KW_NO_POINTS:
    points = KW_POINTS_CORRECT
#  print 'choice_s_to_choice: points = ', points

  body = tokens.get_body(choice)
#  print 'body:', explain

  # Special marked KW_POINT_CORRECT indicates that this is
  # a correct choice.
  block = blocks.Choice({tokens.KEY_POINTS:[points], \
                         tokens.KEY_BODY:body, \
                         tokens.KEY_EXPLAIN:explain})
  return block.to_string()

# Translate a simple select to select
def simple_select_to_select(toks):
#  print 'simple_select_to_select:', toks
  # select is a list of point (optional) and  body string
  select = tokens.get_sel(toks)
#  print 'select:', select

  explain = tokens.get_explain(toks)
#  print 'explain:', explain
  # points is optional

  points = tokens.get_points_opt(select)
#  print 'simple_select_to_answer: points = ', points
  body = tokens.get_body(select)
  block = blocks.Select({tokens.KEY_POINTS:[points], \
                           tokens.KEY_BODY:body, \
                           tokens.KEY_EXPLAIN:explain})
  return block.to_string()

# Translate a simple select_s (star select) to select
def simple_select_s_to_select(toks):
#  print 'simple_select_s_to_select:', toks
  # select is a  body string
  select = tokens.get_sel(toks)
#  print 'select:', select

  explain = tokens.get_explain(toks)
#  print 'explain:', explain
  # points is optional

  ## Figure points: if points are not provided
  ## They get fuls score
  points = tokens.get_points_opt(select)
  if points == KW_NO_POINTS:
    points = KW_POINTS_CORRECT
#  print 'choice_s_to_choice: points = ', points

  body = tokens.get_body(select)
#  print 'body:', explain

  # Special marked KW_POINT_CORRECT indicates that this is
  # a correct select.
  block = blocks.Select({tokens.KEY_POINTS:[points], \
                         tokens.KEY_BODY:body, \
                         tokens.KEY_EXPLAIN:explain})
  return block.to_string()



## END Globals
######################################################################


# a block of text between dollar signs
parser_math_block = kw_dollar + pp.Word(pp.printables) + kw_dollar


######################################################################
## BEGIN: keywords, headings, numbers 

#text_block = pp.Word(pp.printables)   

# inline answer, using "ans" throughout to distinguish
com_answer = pp.Literal(dex.COM_ANSWER)
com_authors = pp.Literal(dex.COM_AUTHORS).suppress()
# begin is used in pp.Skip so cannot bu suppresed it seems
com_begin = pp.Literal(COM_BEGIN)
com_course_number = pp.Literal(dex.COM_COURSE_NUMBER).suppress()
com_duedate = pp.Literal(dex.COM_DUEDATE).suppress()
com_document_class = pp.Literal(dex.COM_DOCUMENT_CLASS)
com_end = pp.Literal(COM_END).suppress()
com_explain = pp.Literal(dex.COM_EXPLAIN)
com_hint = pp.Literal(dex.COM_HINT)
com_no = pp.Literal(COM_NO).suppress()
com_picture = pp.Literal(dex.COM_PICTURE).suppress()
#  Used in pp.Skip, so this probably can't be suppressed 
com_points = pp.Literal(dex.COM_POINTS)
#  Used in pp.Skip, so this probably can't be suppressed 
com_prompt = pp.Literal(dex.COM_PROMPT)
com_info = pp.Literal(dex.COM_INFO)
com_provides_book = pp.Literal(dex.COM_PROVIDES_BOOK).suppress()
com_provides_chapter = pp.Literal(dex.COM_PROVIDES_CHAPTER).suppress()
com_provides_assignment = pp.Literal(dex.COM_PROVIDES_ASSIGNMENT).suppress()
com_provides_section = pp.Literal(dex.COM_PROVIDES_SECTION).suppress()
com_provides_unit = pp.Literal(dex.COM_PROVIDES_UNIT).suppress()
com_semester = pp.Literal(dex.COM_SEMESTER).suppress()
#com_solution = pp.Literal(dex.COM_SOLUTION)
com_title = pp.Literal(dex.COM_TITLE).suppress()
com_unique = pp.Literal(COM_UNIQUE).suppress()
com_website = pp.Literal(dex.COM_WEBSITE).suppress()
com_begin_questionfr = pp.Literal(mk_str_begin(dex.QUESTION_FR))
com_begin_questionmc = pp.Literal(mk_str_begin(dex.QUESTION_MC))



# These have to be keywords because otherwise
com_choice = pp.Keyword(dex.COM_CHOICE)
com_choice_s = pp.Keyword(dex.COM_CHOICE_S)
com_select = pp.Keyword(dex.COM_SELECT)
com_select_s = pp.Keyword(dex.COM_SELECT_S)



## END Globals
######################################################################


######################################################################
## BEGIN Class Parser


class Parser:
   
  # DEPRECATED.  DOES NOT WORK PROBABLY BECAUSE 
  # IT RELIES ON WHITESPACE
  #
  # # Match a block of text (returned as string) until and excluning allbut.
  # def mk_parser_text_block (self, allbut):
  #   # TODO: if you don't suppress lineend, you robably don't have to join 
  #   block = pp.OneOrMore(pp.NotAny(allbut) + pp.restOfLine() + pp.lineEnd.suppress())
  #   block.setParseAction(lambda x: '\n'.join(x.asList()))
  #   block = tokens.set_key_body(block)
  #   block.setDebug()
  #   return block

  def mk_parser_begin_any_atom(self):
    result = mk_parser_begin(dex.ALGO) | \
             mk_parser_begin(dex.ALGORITHM) | \
             mk_parser_begin(dex.CODE) | \
             mk_parser_begin(dex.COROLLARY) | \
             mk_parser_begin(dex.COST_SPEC) | \
             mk_parser_begin(dex.DATATYPE) | \
             mk_parser_begin(dex.DATASTR) | \
             mk_parser_begin(dex.DEFINITION) | \
             mk_parser_begin(dex.EXAMPLE) | \
             mk_parser_begin(dex.EXERCISE) | \
             mk_parser_begin(dex.HINT) | \
             mk_parser_begin(dex.IMPORTANT) | \
             mk_parser_begin(dex.LEMMA) | \
             mk_parser_begin(dex.NOTE) | \
             mk_parser_begin(dex.PARAGRAPH) | \
             mk_parser_begin(dex.PROBLEM) | \
             mk_parser_begin(dex.PROOF) | \
             mk_parser_begin(dex.PROPOSITION) | \
             mk_parser_begin(dex.REMARK) | \
             mk_parser_begin(dex.SOLUTION) | \
             mk_parser_begin(dex.SYNTAX) | \
             mk_parser_begin(dex.TEACH_ASK) | \
             mk_parser_begin(dex.TEACH_NOTE) | \
             mk_parser_begin(dex.THEOREM)
    return result    


  # Match a block of text (returned as string) until and excluding target.
  def mk_parser_text_block (self, target):
    block = pp.SkipTo(target)
    block = tokens.set_key_body(block)
#    block.setDebug()
    return block

  def mk_parser_picture(self):
    # picture
    picture = com_picture + mk_parser_arg(exp_phrase_gram_latex)
    picture = tokens.set_key_picture(picture)
#    picture.setDebug()
    return picture

  def mk_parser_provides_book(self):
    # picture
    provides = com_provides_book + mk_parser_arg(exp_number)
    provides = com_provides_book + mk_parser_arg(exp_phrase_gram_latex)
    provides = tokens.set_key_provides_book(provides)
#    picture.setDebug()
    return provides

  def mk_parser_provides_chapter(self):
    # picture
    provides = com_provides_chapter + mk_parser_arg(exp_number)
    provides = pp.Optional(com_provides_chapter + mk_parser_arg(exp_number))
    provides = tokens.set_key_provides_chapter(provides)
#    picture.setDebug()
    return provides

  def mk_parser_provides_section(self):
    # picture
    provides = com_provides_section + mk_parser_arg(exp_number)
    provides = pp.Optional(com_provides_section + mk_parser_arg(exp_number))
    provides = tokens.set_key_provides_section(provides)
#    picture.setDebug()
    return provides

  def mk_parser_provides_unit(self):
    # picture
    provides = com_provides_unit + mk_parser_arg(exp_number)
    provides = pp.Optional(com_provides_unit + mk_parser_arg(exp_number))
    provides = tokens.set_key_provides_unit(provides)
#    picture.setDebug()
    return provides

  def mk_parser_provides_assignment(self):
    provides = com_provides_assignment + mk_parser_arg(exp_number)
    provides = pp.Optional(com_provides_assignment + mk_parser_arg(exp_number))
    provides = tokens.set_key_provides_assignment(provides)
    return provides

  def mk_parser_semester(self):
    # semester
    semester = com_semester + mk_parser_arg(exp_phrase_latex)
    semester = tokens.set_key_semester(semester)
#    semester.setDebug()
    return semester

  def mk_parser_website(self):
    # website
    website = com_website + mk_parser_arg(exp_phrase_latex)
    website = tokens.set_key_website(website)
#    website.setDebug()
    return website

  def mk_parser_lnp (self): 
    if self.labels_optional: 
      label = pp.Optional(exp_label)
    else: 
      label = exp_label
    label = tokens.set_key_label(label)
#    label = label.setDebug()

    if self.uniques_optional: 
      un = pp.Optional(self.exp_unique)
    else: 
      un = self.exp_unique
    un = tokens.set_key_unique(un)
#    no.setDebug()

    parents = pp.ZeroOrMore(exp_parent)
    parents = tokens.set_key_parents(parents)
#    parents.setDebug()

    return (label, no, parents)

  # TODO: elim this
  def mk_parser_no_deprecated (self):
    no = com_no + mk_parser_arg(exp_number)
    if self.nos_optional: 
      no = pp.Optional(exp_number)
    no = tokens.set_key_no(no)
#    no.setDebug()
    return no

  ## TODO: elim this
  def mk_parser_lup_deprecated (self): 
    if self.labels_optional: 
      label = pp.Optional(exp_label)
    else: 
      label = exp_label
    label = tokens.set_key_label(label)
#    label = label.setDebug()

    if self.uniques_optional: 
      un = pp.Optional(self.exp_unique)
    else: 
      un = self.exp_unique
    un = tokens.set_key_unique(un)
#    no.setDebug()

    parents = pp.ZeroOrMore(exp_parent)
    parents = tokens.set_key_parents(parents)
#    parents.setDebug()

    return (label, un, parents)

  def mk_parser_lnup (self): 
    if self.labels_optional: 
      label = pp.Optional(exp_label)
    else: 
      label = exp_label
    label = tokens.set_key_label(label)
#    label = label.setDebug()

    if self.nos_optional: 
      no = pp.Optional(com_no + mk_parser_arg(exp_number))
    else:
      no = com_no + mk_parser_arg(exp_number)

    no = tokens.set_key_no(no)
#    no.setDebug()

    if self.uniques_optional: 
      un = pp.Optional(self.exp_unique)
    else: 
      un = self.exp_unique
    un = tokens.set_key_unique(un)
#    no.setDebug()

    parents = pp.ZeroOrMore(exp_parent)
    parents = tokens.set_key_parents(parents)
#    parents.setDebug()

    return (label, no, un, parents)
   
  # Make begin & end keywords, title
  def mk_parsers_common(self, dex_name, block_name): 

    def process_begin(x):
      result = self.process_block_begin(block_name,x[0])
      return result

    def process_end(x):
      result = self.process_block_end(block_name,x[0])
      return result

    begin = mk_parser_begin(dex_name)
#    begin = begin.setParseAction(curry(self.process_block_begin, block_name))
    begin = begin.setParseAction(process_begin)
    begin = tokens.set_key_begin(begin)

    end = mk_parser_end(dex_name)
    end = end.setParseAction(curry(self.process_block_end, block_name))
    end = end.setParseAction(process_end)
    end = tokens.set_key_end(end)

    # the title is set to be contents of the arg so i should be
    # able to extract it from tokens without [0] but i need it
    # for some reason
    title = mk_parser_opt_arg(exp_title)
    if self.titles_optional: 
#      print "titles are optional"
      title = pp.Optional(title)
    else:
 #     print "titles are not optional"
      pass

    title = tokens.set_key_title(title)
#    title = title.setDebug()

    (label, no, un, parents) = self.mk_parser_lnup()
    return (begin, end, title, label, no, un, parents)

  # Parser for course
  def mk_parser_course (self):
    document_class = com_document_class

    # Make it a group to provide uniform access with optional titles
    title_latex = tokens.set_key_title(pp.Group(exp_title_latex))
    title = com_title + mk_parser_arg(title_latex)

    (label, no, unique, parents) = self.mk_parser_lnup()
 
    # course number
    number = tokens.set_key_course_number(exp_number)
#    arg_course_number_curly = mk_parser_arg(dash_separated_number)
    arg_course_number_curly = mk_parser_arg(number)
    course_number = com_course_number + arg_course_number_curly


    about = self.mk_parser_text_block(com_begin)
    about = pp.Optional(about)
    about = about.setParseAction(lambda x: x[0])
    about = tokens.set_key_joker(about)
#    about.setDebug()

    picture = self.mk_parser_picture ()
    pb = self.mk_parser_provides_book ()
    pc = self.mk_parser_provides_chapter ()
    ps = self.mk_parser_provides_section ()
    pu = self.mk_parser_provides_unit ()
    pa = self.mk_parser_provides_assignment ()

    semester = self.mk_parser_semester ()
    website = self.mk_parser_website ()

    ## IMPORTANT: book is not nested inside of a course  
    ## This enables matching a course before a book.
    ## This makes it possible to set things like labels
    ## more effectively during elaboration.
    ##
    contents =  tokens.set_key_contents(self.exp_book)

    if self.course_label_on: 
      course =  document_class + \
                title + \
                (label & no & unique & parents) + \
                (course_number & \
                 picture & \
                 pb & pc & ps & pu & pa & \
                 semester & \
                 website) + \
                 about 

    else: 
      course =  document_class + \
                title + \
                (no & unique & parents) + \
                (course_number & \
                 picture & \
                 pb & pc & ps & pu & pa & \
                 semester & \
                 website) + \
                 about 

    course.setParseAction(self.process_course)
    return course

  # Parser for book
  def mk_parser_book (self):
    book_begin = mk_parser_begin(dex.BOOK)
    book_begin = book_begin.setParseAction(curry(self.process_block_begin,Block.BOOK))

    book_end = mk_parser_end(dex.BOOK)
    book_end = book_end.setParseAction(curry(self.process_block_end,Block.BOOK))

    # Make it a group to provide uniform access with optional titles
    title_latex = tokens.set_key_title(pp.Group(exp_title_latex))
#    title_latex = tokens.set_key_title(exp_title_latex)
    title = com_title + mk_parser_arg(title_latex)

    (label, no, unique, parents) = self.mk_parser_lnup()
#    label.setDebug()
#    no.setDebug()
#    parents.setDebug()


    exp_authors_keyed = tokens.set_key_authors(exp_authors)
    authors = com_authors + mk_parser_arg(exp_authors_keyed)

    contents = tokens.set_key_contents(self.exp_chapters)
#    contents = contents.setDebug()
    asst = tokens.set_key_assignment(self.exp_assignments)

    # Wrap it inside a group so that the 
    # course can assign a contents key it without updating the book contents
    book = book_begin + \
           title + \
           (label & no & unique & parents) + \
           authors + \
           contents + \
           asst + \
           book_end

    book = tokens.set_key_chapter(book)

    book.setParseAction(self.process_book)
    return book

  # Parser for chapter
  def mk_parser_chapter (self):
    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.CHAPTER, Block.CHAPTER)
    picture = self.mk_parser_picture ()

    begin_section = mk_parser_begin(dex.SECTION)
    # intro is the part up to the first section
    intro = self.mk_parser_text_block(begin_section | end)
    intro = pp.Optional(intro)
    intro = intro.setParseAction(lambda x: x[0])
    intro = tokens.set_key_intro(intro)
#    about.setDebug()

    contents = tokens.set_key_contents(self.exp_sections)
#    contents = contents.setDebug()

    chapter = begin + \
              title + \
              (label & no & unique & parents) + \
              picture + \
              intro + \
              contents + \
              end
 
    chapter = tokens.set_key_chapter(chapter)
    chapter.setParseAction(self.process_chapter)

    return chapter


  # Parser for section
  def mk_parser_section (self):
    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.SECTION, Block.SECTION)
    
    begin_unit = mk_parser_begin(dex.UNIT)
    # intro is the part up to the first unit
    intro = self.mk_parser_text_block(begin_unit | end)
    intro = pp.Optional(intro)
    intro = intro.setParseAction(lambda x: x[0])
    intro = tokens.set_key_intro(intro)
#    about.setDebug()

    contents = tokens.set_key_contents(self.exp_units)

    section = begin + title + \
             (label & no & unique & parents) + \
              intro + \
              contents + \
              end
    section = tokens.set_key_section(section)

    section.setParseAction(self.process_section)
    return section


  # Parser for group
  def mk_parser_group (self):
    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.GROUP, Block.GROUP)

    contents = self.exp_atoms
    contents = tokens.set_key_group_contents(contents)
 #   contents.setDebug()
    group = begin + \
            title + \
            (label & no & unique & parents) + \
            contents + \
            end
    group = tokens.set_key_group(group)
    group.setParseAction(self.process_group)

    return group

  # Parser for unit
  def mk_parser_unit (self):
    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.UNIT, Block.UNIT)

    contents = tokens.set_key_contents(self.exp_elements)

    checkpoint = pp.Optional(self.exp_checkpoint)
    checkpoint = tokens.set_key_checkpoint(checkpoint)

    unit = begin + \
           title + \
           (label & no & unique & parents) +\
           contents + \
           checkpoint + \
           end
    unit = tokens.set_key_unit(unit)
    unit.setParseAction(self.process_unit)

    return unit
  
  # Parser for checkpoint
  def mk_parser_checkpoint (self):
    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.CHECKPOINT, Block.CHECKPOINT)

    contents = tokens.set_key_contents(self.exp_questions)
#    contents.setDebug()

    checkpoint = \
      begin + \
      title + \
      (label & no & unique  & parents) + \
      contents + \
      end
   
    checkpoint = tokens.set_key_checkpoint(checkpoint)
    checkpoint.setParseAction(self.process_checkpoint)

    return checkpoint

  # Make a parser for an assignment
  def mk_parser_assignment (self):
    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.ASSIGNMENT, Block.ASSIGNMENT)

    title_latex = tokens.set_key_title(exp_title_latex)
    title = com_title + mk_parser_arg(title_latex)

    # using the title latex?
    exp_duedate_latex = exp_title_latex
    duedate_latex = tokens.set_key_duedate(exp_duedate_latex)
    duedate = com_duedate + mk_parser_arg(duedate_latex)

    contents = tokens.set_key_contents(self.exp_asstproblems)

    assignment = begin + \
                 title + \
                 (label & no & unique & parents) + \
                 duedate + \
                 contents + \
                 end
    assignment = tokens.set_key_assignment(assignment)
    assignment.setParseAction(self.process_assignment)
    return assignment

  # Make a parser for a problem
  def mk_parser_asstproblem (self):
    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.ASSTPROBLEM, Block.ASSTPROBLEM)

    title_latex = tokens.set_key_title(exp_title_latex)
    title = com_title + mk_parser_arg(title_latex)

    contents = tokens.set_key_contents(self.exp_questions)

    info = com_info.suppress() + self.mk_parser_text_block(com_begin_questionfr | com_begin_questionmc)
    info = info * (0, 1)
    info = info.setParseAction(lambda x: (NEWLINE.join(x.asList())))
    info = tokens.set_key_info(info)

    problem = begin + \
              title + \
              (label & no & unique & parents) + \
              info + \
              contents + \
              end
    problem = tokens.set_key_asstproblem(problem)
    problem.setParseAction(self.process_asstproblem)
    return problem

  # Make parser for an algorithm
  def mk_parser_algo (self, process_algo):
    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.ALGO, Block.ALGO)

#    begin.setDebug()
#    end.setDebug()
    
    # a line of the body is a line of text that does not start with 
    # \end{algo}
    # combining leads to dropping of initial spaces 
    # body_line = pp.Combine(~end + pp.restOfLine() + pp.lineEnd())
    body_line = ~end + pp.restOfLine() + pp.lineEnd().suppress()

    # Body is multiple lines
    body = pp.ZeroOrMore(body_line)
    body = tokens.set_key_body(body)
#    body.setDebug()
 
    # Algo cannot be nested
    algo = begin + \
           title + \
           (label & no & unique & parents) + \
           body + \
           end
    algo.setParseAction(process_algo)
    return algo

  # Make parser for an atom
  def mk_parser_atom (self, atom_name, process_atom):
    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (atom_name, Block.ATOM)

    atom_end_str = mk_str_end(atom_name)
    atom_body = pp.SkipTo(atom_end_str) 
    atom_body = tokens.set_key_body(atom_body)
    # Atom's cannot be nested.
    atom = begin + \
           title + \
           (label & no & unique & parents) + \
           atom_body + \
           end
    atom.setParseAction(process_atom)

    return atom

  # Make parser for an answer
  def mk_parser_answer (self, process_answer):
    (begin, end, title__, label, no, unique, parents) = self.mk_parsers_common (dex.ANSWER, Block.ANSWER)

    # points is optional argument, will be interpreted as 0 of missing.
    points = mk_parser_opt_arg(exp_number)
    points = pp.Optional(points)
    points = tokens.set_key_points(points)
#    points.setDebug()

    # titles can be provided by with extra keyword, always optional
    # Make it a group to provide uniform access with optional titles
    title_latex = tokens.set_key_title(pp.Group(exp_title_latex))
#    title_latex = tokens.set_key_title(exp_title_latex)
    title = com_title + mk_parser_arg(title_latex)
    title = pp.Optional(title)

    # answer body
    body = self.mk_parser_text_block(com_explain | end)
    body = tokens.set_key_body(body)
#    body.setDebug()
   
    # explaination, optional
    explain = com_explain.suppress() + self.mk_parser_text_block (end)
    explain = pp.Optional(explain)
    # because of the optional, we need to handle it again
    explain = explain.setParseAction(lambda x: '\n'.join(x.asList()))
    explain = tokens.set_key_explain(explain)
#    explain.setDebug()

    answer = begin + points + \
             (label & no & unique & parents) + \
             title + \
             body + \
             explain + \
             end

    answer.setParseAction(process_answer)
    answer = tokens.set_key_answer(answer)
#    answer.setDebug()
    return answer

  # Make parser for a choice
  def mk_parser_choice (self, process_choice):
    (begin, end, title__, label, no, unique, parents) = self.mk_parsers_common (dex.CHOICE, Block.CHOICE)

    # points is optional argument, will be interpreted as 0 of missing.
    points = mk_parser_opt_arg(exp_integer_number)
    points = pp.Optional(points)
    points = tokens.set_key_points(points)
#    points.setDebug()

    # titles can be provided by with extra keyword, always optional
    # Make it a group to provide uniform access with optional titles
    title_latex = tokens.set_key_title(pp.Group(exp_title_latex))
#    title_latex = tokens.set_key_title(exp_title_latex)
    title = com_title + mk_parser_arg(title_latex)
    title = pp.Optional(title)

    # choice body
    body = self.mk_parser_text_block(com_explain | end)
    body = tokens.set_key_body(body)
#    body.setDebug()
   
    # explaination, optional
    explain = com_explain.suppress() + self.mk_parser_text_block (com_hint | end)
    explain = pp.Optional(explain)
    # because of the optional, we need to handle it again
    explain = explain.setParseAction(lambda x: '\n'.join(x.asList()))
    explain = tokens.set_key_explain(explain)
#    explain.setDebug()

    choice = begin + points + \
             (label & no & unique & parents) + \
             title + \
             body + \
             explain + \
           end

    choice.setParseAction(process_choice)
    choice = tokens.set_key_choice(choice)
#    choice.setDebug()
    return choice

  # Make parser for a select
  def mk_parser_select (self, process_select):
    (begin, end, title__, label, no, unique, parents) = self.mk_parsers_common (dex.SELECT, Block.CHOICE)

    # points is optional argument, will be interpreted as 0 of missing.
    points = mk_parser_opt_arg(exp_integer_number)
    points = pp.Optional(points)
    points = tokens.set_key_points(points)
#    points.setDebug()

    # titles can be provided by with extra keyword, always optional
    # Make it a group to provide uniform access with optional titles
    title_latex = tokens.set_key_title(pp.Group(exp_title_latex))
#    title_latex = tokens.set_key_title(exp_title_latex)
    title = com_title + mk_parser_arg(title_latex)
    title = pp.Optional(title)

    # select body
    body = self.mk_parser_text_block(com_explain | end)
    body = tokens.set_key_body(body)
#    body.setDebug()
   
    # explaination, optional
    explain = com_explain.suppress() + self.mk_parser_text_block (com_hint | end)
    explain = pp.Optional(explain)
    # because of the optional, we need to handle it again
    explain = explain.setParseAction(lambda x: '\n'.join(x.asList()))
    explain = tokens.set_key_explain(explain)
#    explain.setDebug()

    select = begin + points + \
             (label & no & unique & parents) + \
             title + \
             body + \
             explain + \
           end

    select.setParseAction(process_select)
    select = tokens.set_key_select(select)
#    select.setDebug()
    return select

  # Make parser for common question elements
  ## TODO: seems like teh stoppers can all be unified as one or perhaps 
  ## two parsers
  def mk_parser_question_elements (self, dex_name): 

    # an element will stop if \end{dex_name} is seen
    end_question = mk_parser_end(dex_name)

    # an element will stop if \begin{answer} is seen
    begin_answer = mk_parser_begin(dex.ANSWER)

    # an element may end at a \begin{choice}
    begin_choice = mk_parser_begin(dex.CHOICE)

    # an element may end at a \begin{select}
    begin_select = mk_parser_begin(dex.SELECT)

    # stoppers
    common_stopper = com_explain | com_hint | com_points | com_prompt | end_question 
    answer_stopper = begin_answer | com_answer | common_stopper
    choice_stopper = begin_choice | com_choice | com_choice_s | common_stopper
    select_stopper = begin_select | com_select | com_select_s | common_stopper
    all_stopper = begin_answer | com_answer | begin_choice | com_choice | com_choice_s | begin_select | com_select | com_select_s | common_stopper

    points = com_points.suppress() + self.mk_parser_text_block(all_stopper)
    points = tokens.set_key_points(points)
    points.setParseAction(lambda x: x[0])
#    points.setDebug()

    # argument points
    arg_points = mk_parser_opt_arg(exp_integer_number)
    arg_points = pp.Optional(arg_points)
    arg_points = tokens.set_key_points(arg_points)  
#    arg_points.setDebug()

    prompt = com_prompt.suppress() + self.mk_parser_text_block (all_stopper)
    prompt = tokens.set_key_prompt(prompt)
    prompt.setParseAction(lambda x: x[0])
#    prompt.setDebug()

    hint = com_hint.suppress() + self.mk_parser_text_block (all_stopper)
    hint = pp.Optional(hint)
    # because of the optional, we need to handle it again
    hint = hint.setParseAction(lambda x: (NEWLINE.join(x.asList())))
    hint = tokens.set_key_hint(hint)
#    hint.setDebug()

    explain = com_explain.suppress() + self.mk_parser_text_block (all_stopper)
    explain = pp.Optional(explain)
    # because of the optional, we need to handle it again
    explain = explain.setParseAction(lambda x: (NEWLINE.join(x.asList())))
    explain = tokens.set_key_explain(explain)
#    explain.setDebug()

    ## BEGIN: Answers 
    # ans body
    ans_body = tokens.set_key_body(self.mk_parser_text_block (answer_stopper))
    ans_body = ans_body.setParseAction(lambda x: (NEWLINE.join(x.asList())))

    # ans, group so that different points don't mix up
    ans = pp.Group(com_answer.suppress() + arg_points + ans_body)
#    ans = pp.Optional(ans)
    # because of the optional, we need to handle it again
#    ans = ans.setParseAction(lambda x: (NEWLINE.join(get_body(x).asList())))
    ans = tokens.set_key_ans(ans)
#    ans.setDebug()
    ## END: Answers


    ## BEGIN: Choices 
    # choi body
    choi_body = tokens.set_key_body(self.mk_parser_text_block(choice_stopper))
#    choi_body.setDebug()
    choi_body = choi_body.setParseAction(lambda x: (NEWLINE.join(x.asList())))

    # choi, group so that different points don't mix up
    choi = pp.Group(com_choice + arg_points + choi_body)
    choi = tokens.set_key_choi(choi)
#    choi.setDebug()

    # choi_s, group so that different points don't mix up
    choi_s = pp.Group(com_choice_s + arg_points + choi_body)
    choi_s = tokens.set_key_choi(choi_s)
#    choi_s.setDebug()
    # ## END: Choices

    ## BEGIN: Selects
    # sel body
    sel_body = tokens.set_key_body(self.mk_parser_text_block(select_stopper))
#    sel_body.setDebug()
    sel_body = sel_body.setParseAction(lambda x: (NEWLINE.join(x.asList())))

    # sel, group so that different points don't mix up
    sel = pp.Group(com_select + arg_points + sel_body)
    sel = tokens.set_key_sel(sel)
#    sel.setDebug()

    # sel_s, group so that different points don't mix up
    sel_s = pp.Group(com_select_s + arg_points + sel_body)
    sel_s = tokens.set_key_sel(sel_s)
#    sel_s.setDebug()
    # ## END: Choices
    
    return (ans, choi, choi_s, explain, hint, points, prompt, sel, sel_s)

  # Make parser for a free-form question
  def mk_parser_question_fr (self, process_question_fr):

    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.QUESTION_FR, Block.QUESTION)

    (ans, choi__, choi_s__, explain, hint, points, prompt, sel__, sel_s__) = self.mk_parser_question_elements (dex.QUESTION_FR)

    simple_answer = ans + explain
#    simple_answer.setName('simple_answer').setResultsName('simple_answer')
#    simple_answer.setDebug()
    # Translate simple answer to a full fledged answer.
    simple_answer.setParseAction(lambda toks:simple_answer_to_answer(toks))

    answer = self.exp_answer | simple_answer
    answers = pp.OneOrMore(answer)
    answers = tokens.set_key_answers(answers)
    answers = answers.setParseAction(lambda xs: NEWLINE.join(xs.asList()))
#    answers.setDebug()

    ## NOTE: EXTREMELY FRAGILE
    ## If answers is included as part of the & pattern, it gets
    ## attempted at every possible location and somehow the match 
    ## gets forgotton.  
    question = \
      (begin + \
       title + \
       (label & no & unique & parents) + \
       (points & prompt & hint) + \
       answers + \
       end) \

    question.setParseAction(process_question_fr)
    question = tokens.set_key_question(question)
 #   question.setDebug()
    return question

  # Make parser for a multi-answer questions
  def mk_parser_question_ma (self, process_question_ma):

    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.QUESTION_MA, Block.QUESTION)

    (ans__, choi__, choi_s__, explain, hint, points, prompt, sel, sel_s) = self.mk_parser_question_elements (dex.QUESTION_MA)

    simple_select = sel + explain
    simple_select.setParseAction(lambda toks:simple_select_to_select(toks))
    simple_select.setName('simple_select')
#    simple_select.setDebug()

    simple_select_s = sel_s + explain
    simple_select_s.setParseAction(lambda toks:simple_select_s_to_select(toks))
    simple_select_s.setName('simple_select_s')
#    simple_select_s.setDebug()

    # Translate simple answer to a full fledged answer.


    # Translate simple answer to a full fledged answer.
    select = self.exp_select | simple_select | simple_select_s 
    selects = pp.OneOrMore(select)
    selects = tokens.set_key_selects(selects)
    selects = selects.setParseAction(lambda xs: NEWLINE.join(xs.asList()))
#    selects.setDebug()


    ## NOTE: EXTREMELY FRAGILE
    ## If answers is included as part of the & pattern, it gets
    ## attempted at every possible location and somehow the match 
    ## gets forgotton.  
    question = \
      (begin + \
       title + \
       (label & no & unique & parents) + \
       (hint & points & prompt) + \
       selects + \
       end) \

    question.setParseAction(process_question_ma)
    question = tokens.set_key_question(question)
#    question.setDebug()
    return question

  # Make parser for a multi-choice questions
  def mk_parser_question_mc (self, process_question_mc):

    (begin, end, title, label, no, unique, parents) = self.mk_parsers_common (dex.QUESTION_MC, Block.QUESTION)

    (ans__, choi, choi_s, explain, hint, points, prompt, sel__, sel_s__) = self.mk_parser_question_elements (dex.QUESTION_MC)

    simple_choice = choi + explain
    simple_choice.setParseAction(lambda toks:simple_choice_to_choice(toks))
    simple_choice.setName('simple_choice')
#    simple_choice.setDebug()

    simple_choice_s = choi_s + explain
    simple_choice_s.setParseAction(lambda toks:simple_choice_s_to_choice(toks))
    simple_choice_s.setName('simple_choice_s')
#    simple_choice_s.setDebug()

    # Translate simple answer to a full fledged answer.

    choice = self.exp_choice | simple_choice | simple_choice_s
    choices = pp.OneOrMore(choice)
    choices = tokens.set_key_choices(choices)
    choices = choices.setParseAction(lambda xs: NEWLINE.join(xs.asList()))
#    choices.setDebug()


    ## NOTE: EXTREMELY FRAGILE
    ## If answers is included as part of the & pattern, it gets
    ## attempted at every possible location and somehow the match 
    ## gets forgotton.  
    question = \
      (begin + \
       title + \
       (label & no & unique & parents) + \
       (hint & points & prompt) + \
       choices + \
       end) \

    question.setParseAction(process_question_mc)
    question = tokens.set_key_question(question)
#    question.setDebug()
    return question


  def __init__(self, \
               labels_optional, \
               nos_optional, \
               uniques_optional, \
               parents_optional, \
               titles_optional, \
               course_label_on, \
               process_block_begin, \
               process_block_end, \
               process_algo,
               process_atom_algorithm, \
               process_atom_code, \
               process_atom_corollary, \
               process_atom_cost_spec, \
               process_atom_datastr, \
               process_atom_datatype, \
               process_atom_definition, \
               process_atom_example, \
               process_atom_exercise, \
               process_atom_hint, \
               process_atom_important, \
               process_atom_lemma, \
               process_atom_note, \
               process_atom_paragraph, \
               process_atom_problem, \
               process_atom_proof, \
               process_atom_proposition, \
               process_atom_remark, \
               process_atom_solution, \
               process_atom_syntax, \
               process_atom_teach_ask, \
               process_atom_teach_note, \
               process_atom_theorem, \
               process_answer, \
               process_choice, \
               process_select, \
               process_book, \
               process_chapter, \
               process_course, \
               process_group, \
               process_question_fr, \
               process_question_ma, \
               process_question_mc, \
               process_checkpoint, \
               process_assignment, \
               process_asstproblem, \
               process_section, \
               process_unit):

    self.labels_optional = labels_optional
    self.nos_optional = nos_optional
    self.uniques_optional = uniques_optional
    self.parents_optional = parents_optional
    self.titles_optional = titles_optional
    self.course_label_on = course_label_on

    self.process_block_begin = process_block_begin              
    self.process_block_end = process_block_end              

    self.process_algo = process_algo
    self.process_answer = process_answer
    self.process_choice = process_choice
    self.process_select = process_select

    self.process_atom_algorithm = process_atom_algorithm
    self.process_atom_code = process_atom_code
    self.process_atom_corollary = process_atom_corollary
    self.process_atom_cost_spec = process_atom_cost_spec
    self.process_atom_datastr = process_atom_datastr
    self.process_atom_datatype = process_atom_datatype
    self.process_atom_definition = process_atom_definition
    self.process_atom_example = process_atom_example
    self.process_atom_exercise = process_atom_exercise
    self.process_atom_hint = process_atom_hint
    self.process_atom_important = process_atom_important
    self.process_atom_lemma = process_atom_lemma
    self.process_atom_note = process_atom_note
    self.process_atom_paragraph = process_atom_paragraph
    self.process_atom_problem = process_atom_problem
    self.process_atom_proposition = process_atom_proposition
    self.process_atom_proof = process_atom_proof
    self.process_atom_remark = process_atom_remark
    self.process_atom_solution = process_atom_solution
    self.process_atom_syntax = process_atom_syntax
    self.process_atom_teach_ask = process_atom_teach_ask
    self.process_atom_teach_note = process_atom_teach_note

    self.process_book = process_book
    self.process_course = process_course
    self.process_group = process_group
    self.process_chapter = process_chapter
    self.process_question_fr = process_question_fr
    self.process_question_ma = process_question_ma
    self.process_question_mc = process_question_mc
    self.process_checkpoint = process_checkpoint
    self.process_assignment = process_assignment
    self.process_asstproblem = process_asstproblem
    self.process_section = process_section
    self.process_unit = process_unit

    # Parser for any begin keyword
    self.begin_any_atom = self.mk_parser_begin_any_atom()

    # Make same basic parsers
    self.exp_unique = com_unique + mk_parser_arg(exp_phrase_gram_latex)

    # answers
    self.exp_answer = self.mk_parser_answer(self.process_answer)
    # group this so that it is returned as a list
    self.exp_answers = pp.ZeroOrMore(self.exp_answer)
    self.exp_answers = tokens.set_key_answers(self.exp_answers)
    self.exp_answers = self.exp_answers.setParseAction(lambda xs: NEWLINE.join(xs.asList()))
    self.exp_answers.setDebug()

    # choices
    self.exp_choice = self.mk_parser_choice(self.process_choice)
    # group this so that it is returned as a list
    self.exp_choices = pp.OneOrMore(self.exp_choice)
    self.exp_choices = tokens.set_key_choices(self.exp_choices)
    self.exp_choices.setParseAction(lambda xs: NEWLINE.join(xs))

    # selects
    self.exp_select = self.mk_parser_select(self.process_select)
    # group this so that it is returned as a list
    self.exp_selects = pp.OneOrMore(self.exp_select)
    self.exp_selects = tokens.set_key_selects(self.exp_selects)
    self.exp_selects.setParseAction(lambda xs: NEWLINE.join(xs))

    # algo's
    self.exp_algo = self.mk_parser_algo(process_algo)

    # Make the atoms
    # Invariant: all atoms have a title
    # Parents are sometimes opitonal sometimes not.
    self.atom_algorithm = self.mk_parser_atom(dex.ALGORITHM, process_atom_algorithm)
    self.atom_code = self.mk_parser_atom(dex.CODE, process_atom_code)
    self.atom_corollary = self.mk_parser_atom(dex.COROLLARY, process_atom_corollary)
    self.atom_cost_spec = self.mk_parser_atom(dex.COST_SPEC, process_atom_cost_spec)
    self.atom_datastr = self.mk_parser_atom(dex.DATASTR, process_atom_datastr)
    self.atom_datatype = self.mk_parser_atom(dex.DATATYPE, process_atom_datatype)
    self.atom_definition = self.mk_parser_atom(dex.DEFINITION, process_atom_definition)
    self.atom_example = self.mk_parser_atom(dex.EXAMPLE, process_atom_example)
    self.atom_exercise = self.mk_parser_atom(dex.EXERCISE,
                                             process_atom_exercise)
    self.atom_hint = self.mk_parser_atom(dex.HINT, process_atom_hint)
    self.atom_important = self.mk_parser_atom(dex.IMPORTANT, process_atom_important)
    self.atom_lemma = self.mk_parser_atom(dex.LEMMA, process_atom_lemma)
    self.atom_note = self.mk_parser_atom(dex.NOTE, process_atom_note)
    self.atom_paragraph = self.mk_parser_atom(dex.PARAGRAPH, process_atom_paragraph)
    self.atom_problem = self.mk_parser_atom(dex.PROBLEM, process_atom_problem)
    self.atom_proof = self.mk_parser_atom(dex.PROOF,  process_atom_proof)
    self.atom_proposition = self.mk_parser_atom(dex.PROPOSITION,  process_atom_proposition)
    self.atom_remark = self.mk_parser_atom(dex.REMARK, process_atom_remark)
    self.atom_solution = self.mk_parser_atom(dex.SOLUTION, process_atom_solution)
    self.atom_syntax = self.mk_parser_atom(dex.SYNTAX, process_atom_syntax)
    self.atom_teach_ask = self.mk_parser_atom(dex.TEACH_ASK, process_atom_teach_ask)
    self.atom_teach_note = self.mk_parser_atom(dex.TEACH_NOTE, process_atom_teach_note)
    self.atom_theorem = self.mk_parser_atom(dex.THEOREM, process_atom_theorem)


    # latexpp atom
    self.exp_atom = self.atom_algorithm | \
                    self.atom_code | \
                    self.atom_corollary | \
                    self.atom_cost_spec | \
                    self.atom_datastr | \
                    self.atom_datatype | \
                    self.atom_definition | \
                    self.atom_example | \
                    self.atom_exercise | \
                    self.atom_hint | \
                    self.atom_important | \
                    self.atom_lemma | \
                    self.atom_note | \
                    self.atom_paragraph | \
                    self.atom_problem | \
                    self.atom_proof | \
                    self.atom_proposition | \
                    self.atom_remark | \
                    self.atom_solution | \
                    self.atom_syntax | \
                    self.atom_teach_ask | \
                    self.atom_teach_note | \
                    self.atom_theorem | \
                    self.exp_algo   # algo's are included as atoms


    # questions
    self.question_fr = self.mk_parser_question_fr(process_question_fr)
    self.question_ma = self.mk_parser_question_ma(process_question_ma)
    self.question_mc = self.mk_parser_question_mc(process_question_mc)


    # dex expression    
    self.exp_atoms = pp.ZeroOrMore(self.exp_atom)
    ## TODO: the next line seems redundant
    self.exp_atoms = self.exp_atoms.ignore(latex_comment)
    self.exp_atoms = self.exp_atoms.setName('exp_atoms').setResultsName('exp_atoms')
    self.exp_atoms.setParseAction(lambda x: '\n'.join(x.asList()))

    # problems expressions
    self.exp_question =  self.question_fr | self.question_ma | self.question_mc
    self.exp_questions = pp.ZeroOrMore(self.exp_question)
    self.exp_questions.setParseAction(lambda x: '\n'.join(x.asList()))
#    self.exp_questions.setDebug()

    # group expressions
    self.exp_group = self.mk_parser_group()
    self.exp_group = self.exp_group.ignore(latex_comment)

    # a unit element is an atom or a  group
    self.exp_elements = pp.ZeroOrMore(self.exp_atom | self.exp_group)
    self.exp_elements.setParseAction(lambda x: '\n'.join(x.asList()))

    # checkpoint expressions
    self.exp_checkpoint = self.mk_parser_checkpoint()

    # asstproblem expression
    self.exp_asstproblem = self.mk_parser_asstproblem()
    self.exp_asstproblem = self.exp_asstproblem.setName('exp_asstproblem').setResultsName('exp_asstproblem')
    self.exp_asstproblems = pp.ZeroOrMore(self.exp_asstproblem)
    self.exp_asstproblems = self.exp_asstproblems.setName('exp_asstproblems').setResultsName('exp_asstproblems')
    self.exp_asstproblems.setParseAction(lambda x: '\n'.join(x.asList()))

    # assignment expresssions
    self.exp_assignment = self.mk_parser_assignment()
    self.exp_assignment = self.exp_assignment.setName('exp_assignment').setResultsName('exp_assignment')
    self.exp_assignments = pp.ZeroOrMore(self.exp_assignment)
    self.exp_assignments = self.exp_assignments.setName('exp_assignments').setResultsName('exp_assignments')
    self.exp_assignments.setParseAction(lambda x: '\n'.join(x.asList()))

    # dex unit
    self.exp_unit = self.mk_parser_unit()
    self.exp_unit = self.exp_unit.setName('exp_unit').setResultsName('exp_unit')
    self.exp_units = pp.ZeroOrMore(self.exp_unit) 
    self.exp_units = self.exp_units.setName('exp_units').setResultsName('exp_units')
    self.exp_units.setParseAction(lambda x: '\n'.join(x.asList()))

    # dex section
    self.exp_section = self.mk_parser_section()
    self.exp_section = self.exp_section.setName('exp_section').setResultsName('exp_section')
    self.exp_section = self.exp_section.setName('exp_section').setResultsName('exp_section')
    self.exp_sections = pp.ZeroOrMore(self.exp_section) 
    self.exp_sections = self.exp_sections.setName('exp_sections').setResultsName('exp_sections')
    self.exp_sections.setParseAction(lambda x: '\n'.join(x.asList()))

    # dex chapter
    self.exp_chapter = self.mk_parser_chapter()
    self.exp_chapter = self.exp_chapter.setName('exp_chapter').setResultsName('exp_chapter')
    self.exp_chapter = self.exp_chapter.setName('exp_chapter').setResultsName('exp_chapter')
    #self.exp_chapter.setDebug()
    self.exp_chapters = pp.ZeroOrMore(self.exp_chapter) 
    self.exp_chapters = self.exp_chapters.setName('exp_chapters').setResultsName('exp_chapters')
    self.exp_chapters.setParseAction(lambda x: '\n'.join(x.asList()))

    # dex book
    self.exp_book = self.mk_parser_book()

    # dex course
    self.exp_course = self.mk_parser_course()

    # document 
    # IMPORTANT: book is not nested inside a course
    # See book parser for details.

    self.document = self.exp_course + self.exp_book + kw_string_end

    # Various modifiers
    self.document = self.document.ignore(latex_comment)
    self.document = self.document.setName('document').setResultsName('document')
  ## END: __init__
## END: class parser

## END Grammar
######################################################################


######################################################################
## BEGIN: parser maker

def mk_uniform_parser (labels_optional, nos_optional, uniques_optional, \
                       parents_optional, titles_optional, \
                       course_label_on, \
                       process_block_begin, \
                       process_block_end, \
                       process_algo, \
                       process_atom, \
                       process_answer, \
                       process_choice, \
                       process_select, \
                       process_book, \
                       process_chapter, \
                       process_course, process_group, \
                       process_question_fr, \
                       process_question_ma, \
                       process_question_mc, \
                       process_checkpoint, \
                       process_assignment, \
                       process_asstproblem, \
                       process_section, process_unit): 

  parser = Parser (\
                        labels_optional, \
                        nos_optional, \
                        uniques_optional, \
                        parents_optional, \
                        titles_optional, \
                        course_label_on, \
                        process_block_begin, \
                        process_block_end, \
                        process_algo, \
                        curry(process_atom, dex.ALGORITHM), \
                        curry(process_atom, dex.CODE), \
                        curry(process_atom, dex.COROLLARY), \
                        curry(process_atom, dex.COST_SPEC), \
                        curry(process_atom, dex.DATASTR), \
                        curry(process_atom, dex.DATATYPE), \
                        curry(process_atom, dex.DEFINITION), \
                        curry(process_atom, dex.EXAMPLE), \
                        curry(process_atom, dex.EXERCISE), \
                        curry(process_atom, dex.HINT), \
                        curry(process_atom, dex.IMPORTANT), \
                        curry(process_atom, dex.LEMMA), \
                        curry(process_atom, dex.NOTE), \
                        curry(process_atom, dex.PARAGRAPH), \
                        curry(process_atom, dex.PROBLEM), \
                        curry(process_atom, dex.PROOF), \
                        curry(process_atom, dex.PROPOSITION), \
                        curry(process_atom, dex.REMARK), \
                        curry(process_atom, dex.SOLUTION), \
                        curry(process_atom, dex.SYNTAX), \
                        curry(process_atom, dex.TEACH_ASK), \
                        curry(process_atom, dex.TEACH_NOTE), \
                        curry(process_atom, dex.THEOREM), \
                        process_answer, \
                        process_choice, \
                        process_select, \
                        process_book, \
                        process_chapter, \
                        process_course, \
                        process_group, \
                        process_question_fr, \
                        process_question_ma, \
                        process_question_mc, \
                        process_checkpoint, \
                        process_assignment, \
                        process_asstproblem, \
                        process_section, \
                        process_unit
                     )

  return parser

## END: parser maker
######################################################################

######################################################################
## Begin: Parser function

def parse (labels_optional, nos_optional, uniques_optional, parents_optional, titles_optional, \
           course_label_on, \
           process_block_begin, \
           process_block_end, \
           process_algo,  \
           process_atom,  \
           process_answer, \
           process_choice, \
           process_select, \
           process_book,  \
           process_chapter, process_course, process_group, \
           process_question_fr, process_question_ma, process_question_mc, \
           process_checkpoint, \
           process_assignment, \
           process_asstproblem, \
           process_section, process_unit, \
           data):

  parser = mk_uniform_parser(labels_optional, nos_optional, uniques_optional, \
                             parents_optional, titles_optional, \
                             course_label_on, \
                             process_block_begin, \
                             process_block_end, \
                             process_algo, \
                             process_atom, \
                             process_answer, \
                             process_choice, \
                             process_select, \
                             process_book, \
                             process_chapter, \
                             process_course, \
                             process_group, \
                             process_question_fr, \
                             process_question_ma, \
                             process_question_mc, \
                             process_checkpoint, \
                             process_assignment, \
                             process_asstproblem, \
                             process_section, \
                             process_unit)

  try:
    result = parser.document.parseString(data)
  except pp.ParseException as pe:
    print "Parse Exception:", pe.line
    print(' '*(pe.col-1) + '^')
    print(pe)

  return result

## End: Parse
######################################################################


######################################################################
## BEGIN Mainline
## This is just a test usage with default processing functions

def process_block_begin (this_block, toks):
  # if this_block == Block.BOOK:
  #   print ('process_block_begin: this block is book')
  # elif this_block == Block.CHAPTER:
  #   print ('process_block_begin: this  block is chapter')
  # elif this_block == Block.SECTION:
  #   print ('process_block_begin: this  block is section')
  # elif this_block == Block.CHECKPOINT:
  #   print ('process_block_begin: this  block is checkpoint')
  # elif this_block == Block.UNIT:
  #   print ('process_block_begin: this  block is unit')
  # elif this_block == Block.ATOM:
  #   print ('process_block_begin: this  block is atom')
  # elif this_block == Block.QUESTION:
  #   print ('process_block_begin: this  block is question')
  # elif this_block == Block.CHOICE:
  #   print ('process_block_begin: this  block is choice')
  # else :
  #   print 'this block is UNKNOWN. Fatal ERROR:', this_block

  return toks

def process_block_end (this_block, toks):
  # if this_block == Block.BOOK:
  #   print ('process_block_end: this  block is book')
  # elif this_block == Block.CHAPTER:
  #   print ('process_block_end: this  block is chapter')
  # elif this_block == Block.CHECKPOINT:
  #   print ('process_block_end: this  block is checkpoint')
  # elif this_block == Block.SECTION:
  #   print ('process_block_end: this  block is section')
  # elif this_block == Block.UNIT:
  #   print ('process_block_end: this  block is unit')
  # elif this_block == Block.ATOM:
  #   print ('process_block_end: this  block is atom')
  # elif this_block == Block.QUESTION:
  #   print ('process_block_begin: this  block is question')
  # elif this_block == Block.CHOICE:
  #   print ('process_block_begin: this  block is choice')
  # else :
  #   print 'process_block_end: this  block is UNKNOWN. Fatal ERROR:', this_block

  return toks

def main(argv):
  labels_optional = True
  nos_optional = True
  uniques_optional = True
  parents_optional = True
  titles_optional = True
  course_label_on = False

  if len(sys.argv) < 2: 
    print 'Usage: dex_parser inputfile [course_label_on = False] [labels_optional = True] [nos_optional = True] [uniques_optional = True] '
    sys.exit()
  elif len(sys.argv) == 2:
    course_label_on = False
    labels_optional = True
    nos_optional = True
    uniques_optional = True
  elif len(sys.argv) == 3:
    print 'course_label_on = ',  sys.argv[2]
    course_label_on = (sys.argv[2] == KW_TRUE)
    labels_optional = True
    nos_optional = True
    uniques_optional = True
  elif len(sys.argv) == 4:
    print 'course_label_on = ',  sys.argv[2]
    print 'labels_optional = ',  sys.argv[3]
    course_label_on = (sys.argv[2] == KW_TRUE)
    labels_optional = (sys.argv[3] == KW_TRUE)
    nos_optional = True
    uniques_optional = True
  elif len(sys.argv) == 5:
    course_label_on = (sys.argv[2] == KW_TRUE)
    labels_optional = (sys.argv[3] == KW_TRUE)
    nos_optional = (sys.argv[4] == KW_TRUE)
    uniques_optional = True
  elif len(sys.argv) == 6:
    course_label_on = (sys.argv[2] == KW_TRUE)
    labels_optional = (sys.argv[3] == KW_TRUE)
    nos_optional = (sys.argv[4] == KW_TRUE)
    uniques_optional = (sys.argv[5] == KW_TRUE)

  else:
    print 'Usage: dex_parser inputfile [course_label_on = False] [labels_optional = True] [nos_optional = True] [uniques_optional = True] '
    sys.exit()

  print 'Executing:', sys.argv[0], str(sys.argv[1]), \
                      'course_label_on = ', course_label_on, \
                      'titles_optional = ', titles_optional, \
                      'labels_optional = ', labels_optional, \
                      'nos_optional = ', nos_optional, \
                      'parents_optional = ', parents_optional, \
                      'uniques_optional = ', uniques_optional

  infile_name = sys.argv[1]
  # drop path stuff
  (path, infile_name) = os.path.split(infile_name) 
  print 'infile_name:', infile_name
  (infile_name_first, infile_ext) = infile_name.split(PERIOD) 
  outfile_name = infile_name_first + '_parsed' + PERIOD + infile_ext

  infile = open(infile_name, 'r')
  outfile = open(outfile_name, 'w')
  data = infile.read ()

  # both labels and numbers are optional
  result = parse (\
             labels_optional, \
             nos_optional, \
             uniques_optional, \
             parents_optional, \
             titles_optional, \
             course_label_on, \
             process_block_begin, \
             process_block_end, \
             blocks.algo_to_string, \
             blocks.atom_to_string, \
             blocks.answer_to_string, \
             blocks.choice_to_string, \
             blocks.select_to_string, \
             blocks.book_to_string, \
             blocks.chapter_to_string, \
             blocks.course_to_string, \
             blocks.group_to_string, \
             blocks.question_fr_to_string, \
             blocks.question_ma_to_string, \
             blocks.question_mc_to_string, \
             blocks.checkpoint_to_string, \
             blocks.assignment_to_string, \
             blocks.asstproblem_to_string, \
             blocks.section_to_string, \
             blocks.unit_to_string, \
             data)

  # The result consists of a course and a book
  course = result[0]
  book = result[1]
  outfile.write(course + NEWLINE + book + NEWLINE)
  outfile.close()
  print 'Parsed code written into file:', outfile_name

if __name__ == '__main__':
    main(sys.argv)