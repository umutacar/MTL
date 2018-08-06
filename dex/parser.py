######################################################################
## dex/parser.py
##
## Provides the "main" function which parses the given 
## dex and translates into to the core language. 
######################################################################

import os
import re
import sys
from functools import partial as curry

import pyparsing as pp 

import pervasives.os_utils as os_utils
from pervasives.parser import *
from pervasives.syntax import *

import syntax as dex
#import dex.pretty_print as dexpp
import blocks as blocks
import tokens as tokens

######################################################################
## BEGIN Globals

# unmarked block 
# has no title, no label, and no parents
def mk_unmarked_block(contents):
  toks = {tokens.KEY_CONTENTS: contents}
  return toks

# Place elements (atoms) under a section
def elements_to_section (toks):
  # There may be no elements in that case return
  if len(toks) > 0:
#    print 'elements_to_section:', toks
    contents = NEWLINE.join(toks.asList()).strip()
#    print 'elements_to_section:', contents

    # make subsubsection
    tokens = mk_unmarked_block (contents)
    block = blocks.Subsubsection(tokens)
    subsubsection = block.to_string()
#    print 'elements_to_section: subsubsection', subsubsection

    # make subsection
    contents = subsubsection
    tokens = mk_unmarked_block (contents)
    block = blocks.Subsection(tokens)
    subsection = block.to_string()
#    print 'elements_to_section: subsection', subsection

    # make section
    contents = subsection
    tokens = mk_unmarked_block (contents)
    block = blocks.Section(tokens)
    section = block.to_string()

    result = section
    return result
  else:
    return toks

# Place elements (atoms) under a section
def elements_to_subsection (toks):
  # There may be no elements in that case return
  if len(toks) > 0:
    contents = NEWLINE.join(toks.asList()).strip()

    # make subsubsection
    tokens = mk_unmarked_block (contents)
    block = blocks.Subsubsection(tokens)
    subsubsection = block.to_string()
#    print 'elements_to_subsection: subsubsection', subsubsection

    # make subsection
    contents = subsubsection
    tokens = mk_unmarked_block (contents)
    block = blocks.Subsection(tokens)
    subsection = block.to_string()
#    print 'elements_to_subsection: subsection', subsection

    result = subsection
    return result
  else:
    return toks

# Place elements (atoms) under a section
def elements_to_subsubsection (toks):
  # There may be no elements in that case return
  if len(toks) > 0:
    contents = NEWLINE.join(toks.asList()).strip()
#    print 'elements_to_subsubsection:', contents

    tokens = mk_unmarked_block (contents)
    block = blocks.Subsubsection(tokens)
    result = block.to_string()
    return result
  else:
    return toks


# Translate a simple answer to an answer
def simple_answer_to_answer(toks):
  print 'simple_ans_to_answer:', toks
  # ans is a list o point (optional) and  body string
  ans = tokens.get_ans(toks)
  print 'ans:', ans
  explain = tokens.get_explain(toks)
  print 'explain:', explain
  # points is optional
  points = tokens.get_points_opt(ans)
  print 'simple_ans_to_answer: points = ', points
  body = tokens.get_body(ans)
  print 'simple_ans_to_answer: body = ', body
  block = blocks.Answer({tokens.KEY_POINTS:points, \
                         tokens.KEY_BODY:body, \
                         tokens.KEY_EXPLAIN:explain})
  result = block.to_string()
  print 'simple_ans_to_answer: result = ', result
  return result

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
com_body = pp.Literal(dex.COM_BODY)
# begin is used in pp.Skip so cannot bu suppresed it seems
com_begin = pp.Literal(COM_BEGIN)
com_course = pp.Literal(dex.COM_COURSE).suppress()
com_duedate = pp.Literal(dex.COM_DUEDATE).suppress()
com_document_class = pp.Literal(dex.COM_DOCUMENT_CLASS)
com_end = pp.Literal(COM_END)
com_explain = pp.Literal(dex.COM_EXPLAIN)
com_folder = pp.Literal(dex.COM_FOLDER)
com_hint = pp.Literal(dex.COM_HINT)
com_instance = pp.Literal(dex.COM_INSTANCE)
com_label = pp.Literal(dex.COM_LABEL)
com_parents = pp.Literal(dex.COM_PARENTS).suppress()
#  Used in pp.Skip, so this probably can't be suppressed 
com_points = pp.Literal(dex.COM_POINTS)
#  Used in pp.Skip, so this probably can't be suppressed 
com_prompt = pp.Literal(dex.COM_PROMPT)
com_info = pp.Literal(dex.COM_INFO)
#com_solution = pp.Literal(dex.COM_SOLUTION)
com_title = pp.Literal(dex.COM_TITLE)
com_topics = pp.Literal(dex.COM_TOPICS)
com_begin_problemfr = pp.Literal(mk_str_begin(dex.PROBLEM_FR))
com_begin_problemmc = pp.Literal(mk_str_begin(dex.PROBLEM_MC))


# These have to be keywords because otherwise
com_choice = pp.Keyword(dex.COM_CHOICE)
com_choice_s = pp.Keyword(dex.COM_CHOICE_S)
com_select = pp.Keyword(dex.COM_SELECT)
com_select_s = pp.Keyword(dex.COM_SELECT_S)



## END Globals
######################################################################

## Parse Actions
def set_parse_action_list_to_text(parser):
  parser = parser.setParseAction(lambda x: (NEWLINE.join(x.asList())).strip())
  return parser

def set_text_block_parse_action(parser):
  parser = parser.setParseAction(lambda x: (NEWLINE.join(x.asList())).strip())
  return parser

def set_text_block_parse_action_single(parser):
  parser = parser.setParseAction(lambda x: x[0].strip())
  return parser




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

  def mk_parser_begin_any_atom_or_group(self):
    result = mk_parser_begin(dex.GROUP) | \
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
             mk_parser_begin(dex.PARAGRAPH_HTML) | \
             mk_parser_begin(dex.PREAMBLE) | \
             mk_parser_begin(dex.PROBLEM) | \
             mk_parser_begin(dex.PROOF) | \
             mk_parser_begin(dex.PROPOSITION) | \
             mk_parser_begin(dex.REMARK) | \
             mk_parser_begin(dex.SKIP) | \
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

  def mk_parser_lp (self): 
    label = pp.Optional(exp_label)
    label = tokens.set_key_label(label)
#    label = label.setDebug()

    parents = pp.ZeroOrMore(exp_parent)
    parents = tokens.set_key_parents(parents)
#    parents.setDebug()

    return (label, parents)
   
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

    (label, parents) = self.mk_parser_lp()
    return (begin, end, title, label, parents)


  # Make begin & end keywords, title
  def mk_parsers_common_pset(self, dex_name, block_name): 
    dex_name = dex.PROBLEM_SET
    block_name = Block.PROBLEM_SET

    def process_begin(x):
      result = self.process_block_begin(block_name,x[0])
      return result

    def process_end(x):
      result = self.process_block_end(block_name,x[0])
      return result

    
    begin = mk_parser_begin(dex_name)
    begin = begin.setParseAction(process_begin)
    begin = tokens.set_key_begin(begin)

    end = mk_parser_end(dex_name)
    end = end.setParseAction(curry(self.process_block_end, block_name))
    end = end.setParseAction(process_end)
    end = tokens.set_key_end(end)

    ## TODO: blend the following in
    ## For lists such as topics and such you can probably use
    ## naive pyhon parser to split the items into lists at spaces or punctionations

    
    # we will stop if \begin{answer} is seen
    kw_begin = pp.Literal(COM_BEGIN)

    # stoppers
    stoppers = kw_begin | end | com_course | com_instance | com_label | com_folder | com_title | com_points | com_topics | com_prompt 
    course = com_course.suppress() + self.mk_parser_text_block (stoppers)
    course = set_text_block_parse_action_single(course)
    course = tokens.set_key_course_number(course)
#    course.setDebug()

    instance = com_instance.suppress() + self.mk_parser_text_block (stoppers)
    instance = set_text_block_parse_action_single(instance)
    instance = tokens.set_key_instance(instance)
#    instance.setDebug()

    
    label = com_label.suppress() + self.mk_parser_text_block (stoppers)
    label = set_text_block_parse_action_single(label)
    label = tokens.set_key_label(label)
#    label.setDebug()

    folder = com_folder.suppress() + self.mk_parser_text_block (stoppers)
    folder = set_text_block_parse_action_single(folder)
    folder = tokens.set_key_folder(folder)
#    folder.setDebug()

    title = com_title.suppress() + self.mk_parser_text_block (stoppers)
    title = set_text_block_parse_action(title)
    title = tokens.set_key_title(title)
#    title.setDebug()

    points = com_points.suppress() + self.mk_parser_text_block (stoppers)
    points = set_text_block_parse_action_single(points)
    points = tokens.set_key_points(points)
#    points.setDebug()
    
    topics = com_topics.suppress() + self.mk_parser_text_block (stoppers)
    topics = set_text_block_parse_action(topics)
    topics = tokens.set_key_topics(topics)
#    topics.setDebug()

    prompt = com_prompt.suppress() + self.mk_parser_text_block (stoppers)
    prompt = set_text_block_parse_action(prompt)
    prompt = tokens.set_key_prompt(prompt)
#    prompt.setDebug()

    return (begin, end, course, instance,  label, folder, points,  prompt, title, topics)
    
  # Parser for problem_sets
  def mk_parser_problem_set (self):
    (begin, end, course, instance, label, folder, points,  prompt, title, topics) = self.mk_parsers_common_pset (dex.PROBLEM_SET, Block.PROBLEM_SET)
    
    contents = pp.ZeroOrMore(self.exp_problem_set_elements)
    contents = tokens.set_key_contents(contents)
    set_parse_action_list_to_text(contents)
#    contents.setDebug()

    problem_set = \
      begin + \
      course + \
      instance + \
      folder + \
      (label & points & title & topics) + \
      prompt + \
      contents + \
      end
   
    problem_set = tokens.set_key_problem_set(problem_set)
    problem_set.setParseAction(self.process_problem_set)
#    problem_set.setDebug()
    return problem_set

  # Parser for chapter
  def mk_parser_chapter (self):
    (begin, end, title, _, parents) = self.mk_parsers_common (dex.CHAPTER, Block.CHAPTER)

    label = exp_label
    label = tokens.set_key_label(label)

    begin_section = mk_parser_begin(dex.SECTION)

    preamble = self.atom_preamble
    # process_atom should be set
    preamble = tokens.set_key_preamble(preamble)
#    about.setDebug()

    # this parse action overwrites that of elements, tok is therefore a list
    elements = self.exp_elements
    elements.setParseAction(elements_to_section)
#    elements.setDebug()

    contents = elements + self.exp_sections
#    contents.setDebug()
    
    set_parse_action_list_to_text(contents)
    contents = tokens.set_key_contents(contents)
#    contents = contents.setDebug()

    chapter = begin + \
              title + \
              (label & parents) + \
              preamble + \
              contents + \
              end
 
    chapter = tokens.set_key_chapter(chapter)
    chapter.setParseAction(self.process_chapter)
#    chapter.setDebug ()
    return chapter


  # Parser for section
  def mk_parser_section (self):
    (begin, end, title, label, parents) = self.mk_parsers_common (dex.SECTION, Block.SECTION)
    
    begin_subsection = mk_parser_begin(dex.SUBSECTION)

    # this parse action overwrites that of elements, tok is therefore a list
    elements = self.exp_elements
    elements.setParseAction(elements_to_subsection)

    contents = elements + self.exp_subsections
    set_parse_action_list_to_text(contents)
    contents = tokens.set_key_contents(contents)

    section = begin + title + \
             (label & parents) + \
              contents + \
              end
    section = tokens.set_key_section(section)

    section.setParseAction(self.process_section)
    return section

  # Parser for subsection
  def mk_parser_subsection (self):
    (begin, end, title, label, parents) = self.mk_parsers_common (dex.SUBSECTION, Block.SUBSECTION)


    elements = self.exp_elements
    elements.setParseAction(elements_to_subsubsection)


    # this parse action overwrites that of elements, tok is therefore a list
    contents = elements + self.exp_subsubsections
    set_parse_action_list_to_text(contents)
    contents = tokens.set_key_contents(contents)

#    contents = self.exp_elements + self.exp_subsubsections
#    set_parse_action_list_to_text(contents)
#    contents = tokens.set_key_contents(contents)
    
    subsection = begin + \
           title + \
           (label & parents) +\
           contents + \
           end
    subsection = tokens.set_key_subsection(subsection)
    subsection.setParseAction(self.process_subsection)

    return subsection


  # Parser for subsection
  def mk_parser_subsubsection (self):
    (begin, end, title, label, parents) = self.mk_parsers_common (dex.SUBSUBSECTION, Block.SUBSUBSECTION)

    contents = tokens.set_key_contents(self.exp_elements)

    block = begin + \
            title + \
            (label & parents) +\
            contents + \
            end
    block = tokens.set_key_subsubsection(block)
    block.setParseAction(self.process_subsubsection)
#    block.setDebug()
    return block

  # Parser for group
  def mk_parser_group (self):
    (begin, end, title, label, parents) = self.mk_parsers_common (dex.GROUP, Block.GROUP)

    contents = self.exp_atoms
    contents = tokens.set_key_group_contents(contents)
 #   contents.setDebug()
    group = begin + \
            title + \
            (label & parents) + \
            contents + \
            end
    group.setParseAction(self.process_group)
    group = tokens.set_key_group(group)

    return group

  # Make parser for an atom
  def mk_parser_atom (self, atom_name, process_atom):
    (begin, end, title, label, parents) = self.mk_parsers_common (atom_name, Block.ATOM)

    atom_end_str = mk_str_end(atom_name)
    atom_body = pp.SkipTo(atom_end_str) 
    atom_body = tokens.set_key_body(atom_body)
    # Atom's cannot be nested.
    atom = begin + \
           title + \
           (label & parents) + \
           atom_body + \
           end
    atom.setParseAction(process_atom)

    return atom

  def mk_parsers_solution_elements (self, dex_name, block_name):

    def process_begin(x):
      result = self.process_block_begin(block_name,x[0])
      return result

    def process_end(x):
      result = self.process_block_end(block_name,x[0])
      return result

    begin = mk_parser_begin(dex_name)
    begin = begin.setParseAction(process_begin)
    begin = tokens.set_key_begin(begin)
#    begin.setDebug ()

    end = mk_parser_end(dex_name)
    end = end.setParseAction(process_end)
#    end = tokens.set_key_end(end)

    # the title is set to be contents of the arg so i should be
    # able to extract it from tokens without [0] but i need it
    # for some reason
    title = mk_parser_opt_arg(exp_title)
    title = pp.Optional(title)
    title = tokens.set_key_title(title)
    title = title.setDebug()

    # stoppers
    common_stopper = begin | com_body | com_explain | com_label | com_points |  com_topics | end 
    answer_stopper =  com_answer 
    choice_stopper = com_choice
    select_stopper = com_select | com_select_s
    all_stoppers = answer_stopper | choice_stopper | select_stopper | common_stopper

    # select body
    body = com_body.suppress() + self.mk_parser_text_block(all_stoppers)
    body = set_text_block_parse_action(body)
    body = tokens.set_key_body(body)
    body.setDebug()

    explain = com_explain.suppress() + self.mk_parser_text_block (all_stoppers)
    explain = pp.Optional(explain)
    # because of the optional, we need to handle it again
    explain = set_text_block_parse_action(explain)
    explain = tokens.set_key_explain(explain)
    explain.setDebug()

    label = com_label.suppress() + self.mk_parser_text_block (all_stoppers)
    label = pp.Optional(label)
    label = set_text_block_parse_action(label)
    label = tokens.set_key_label(label)
    label.setDebug()
    
    points = com_points.suppress() + self.mk_parser_text_block(all_stoppers)
    points = pp.Optional(points, default=KW_NO_POINTS)
    points = set_text_block_parse_action(points)
    points = tokens.set_key_points(points)
    points.setDebug()

    return (begin, end, body, explain, label, points, title)

  # Make parser for an answer
  def mk_parser_answer (self, process_answer):
    (begin, end, body, explain, label, points, title) = self.mk_parsers_solution_elements (dex.ANSWER, Block.ANSWER)

    answer = begin + title + \
             (points & label) + \
             body + \
             explain + \
           end

    answer.setParseAction(process_answer)
    answer = tokens.set_key_answer(answer)
    answer.setDebug()
    return answer

  # Make parser for a choice
  def mk_parser_choice (self, process_choice):
    (begin, end, body, explain, label, points, title) = self.mk_parsers_solution_elements (dex.CHOICE, Block.CHOICE)

    choice = begin + title + \
             (label & points) + \
             body + \
             explain + \
           end

    choice.setParseAction(process_choice)
    choice = tokens.set_key_choice(choice)
 #   choice.setDebug()
    return choice


  # Make parser for a select
  def mk_parser_select (self, process_select):
    (begin, end, body, explain, label, points, title) = self.mk_parsers_solution_elements (dex.SELECT, Block.SELECT)

    select = begin + title + \
             (label & points) + \
             body + \
             explain + \
           end

    select.setParseAction(process_select)
    select = tokens.set_key_select(select)
 #   select.setDebug()
    return select

  # Make parser for common problem elements
  ## TODO: seems like teh stoppers can all be unified as one or perhaps 
  ## two parsers
  def mk_parser_problem_elements (self, dex_name, block_name): 

    def process_begin(x):
      result = self.process_block_begin(block_name,x[0])
      return result

    def process_end(x):
      result = self.process_block_end(block_name,x[0])
      return result
    
    begin = mk_parser_begin(dex_name)
    begin = begin.setParseAction(process_begin)
    begin = tokens.set_key_begin(begin)
    begin.setDebug()

    end = mk_parser_end(dex_name)
    end = end.setParseAction(process_end)
    end = tokens.set_key_end(end)


    # an element will stop if \begin{answer} is seen
    begin_answer = mk_parser_begin(dex.ANSWER)

    # an element may end at a \begin{choice}
    begin_choice = mk_parser_begin(dex.CHOICE)

    # an element may end at a \begin{select}
    begin_select = mk_parser_begin(dex.SELECT)

    # stoppers
    common_stopper = com_explain | com_hint | com_label | com_points | com_prompt |  com_topics | end 
    answer_stopper = begin_answer | com_answer | common_stopper
    choice_stopper = begin_choice | com_choice | com_choice_s | common_stopper
    select_stopper = begin_select | com_select | com_select_s | common_stopper
    all_stopper = begin_answer | com_answer | begin_choice | com_choice | com_choice_s | begin_select | com_select | com_select_s | common_stopper

    points = com_points.suppress() + self.mk_parser_text_block(all_stopper)
    points = set_text_block_parse_action_single(points)
    points = tokens.set_key_points(points)
    points.setDebug()

    label = com_label.suppress() + self.mk_parser_text_block (all_stopper)
    label = set_text_block_parse_action_single(label)
    label = tokens.set_key_label(label)
    label.setDebug()

    topics = com_topics.suppress() + self.mk_parser_text_block (all_stopper)
    topics = pp.Optional (topics)
    topics = set_text_block_parse_action(topics)
    topics = tokens.set_key_topics(topics)

#    topics.setDebug()

    # the title is set to be contents of the arg so i should be
    # able to extract it from tokens without [0] but i need it
    # for some reason
    title = mk_parser_opt_arg(exp_title)
    title = pp.Optional(title)
    title = tokens.set_key_title(title)
    title = title.setDebug()

    # title = com_title.suppress() + self.mk_parser_text_block (all_stopper)
    # title = pp.Optional(title)
    # title = tokens.set_key_title(title)
    # title.setParseAction(lambda x: (NEWLINE.join(x.asList())))
    # title.setDebug()

    # argument points
    arg_points = mk_parser_opt_arg(exp_integer_number)
    arg_points = pp.Optional(arg_points, default = KW_NO_POINTS)
    arg_points = tokens.set_key_points(arg_points)  
#    arg_points.setDebug()

    prompt = com_prompt.suppress() + self.mk_parser_text_block (all_stopper)
    prompt = set_text_block_parse_action(prompt)
    prompt = tokens.set_key_prompt(prompt)
#    prompt.setDebug()

    hint = com_hint.suppress() + self.mk_parser_text_block (all_stopper)
    hint = pp.Optional(hint)
    # because of the optional, we need to handle it again
    hint = set_text_block_parse_action(hint)
    hint = tokens.set_key_hint(hint)
#    hint.setDebug()

    explain = com_explain.suppress() + self.mk_parser_text_block (all_stopper)
    explain = pp.Optional(explain)
    # because of the optional, we need to handle it again
    explain = set_text_block_parse_action(explain)
    explain = tokens.set_key_explain(explain)
#    explain.setDebug()

    ## BEGIN: Answers 
    # ans body
    ans_body = self.mk_parser_text_block (answer_stopper)
    ans_body = set_text_block_parse_action(ans_body)
    ans_body = tokens.set_key_body(ans_body)
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
    choi_body = self.mk_parser_text_block(choice_stopper)
    choi_body = set_text_block_parse_action(choi_body)
    choi_body = tokens.set_key_body(choi_body)
#    choi_body.setDebug()


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
    sel_body = self.mk_parser_text_block(select_stopper)
    sel_body = set_text_block_parse_action(sel_body)
    sel_body = tokens.set_key_body(sel_body)
#    sel_body.setDebug()


    # sel, group so that different points don't mix up
    sel = pp.Group(com_select + arg_points + sel_body)
    sel = tokens.set_key_sel(sel)
#    sel.setDebug()

    # sel_s, group so that different points don't mix up
    sel_s = pp.Group(com_select_s + arg_points + sel_body)
    sel_s = tokens.set_key_sel(sel_s)
#    sel_s.setDebug()
    # ## END: Choices
    
    return (begin, end, ans, choi, choi_s, explain, hint, label, points, prompt, sel, sel_s, title, topics)

  # Make parser for a free-form problem
  def mk_parser_problem_fr (self, process_problem_fr):

    (begin, end, ans, choi__, choi_s__, explain, hint, label, points, prompt, sel__, sel_s__, title, topics) = self.mk_parser_problem_elements (dex.PROBLEM_FR, Block.PROBLEM_FR)

    simple_answer = ans + explain
#    simple_answer.setName('simple_answer').setResultsName('simple_answer')
#    simple_answer.setDebug()
    # Translate simple answer to a full fledged answer.
    simple_answer.setParseAction(lambda toks:simple_answer_to_answer(toks))

    answer = self.exp_answer | simple_answer
    answers = pp.OneOrMore(answer)
    answers = answers.setParseAction(lambda xs: NEWLINE.join(xs.asList()))
    answers = tokens.set_key_answers(answers)
    answers.setDebug()

    ## NOTE: EXTREMELY FRAGILE
    ## If answers is included as part of the & pattern, it gets
    ## attempted at every possible location and somehow the match 
    ## gets forgotton.  
    problem = \
      (begin + \
       title + \
       (label  & points & topics) + \
       (prompt & hint) + \
       answers + \
       end) \

    problem.setParseAction(process_problem_fr)
    problem = tokens.set_key_problem(problem)
 #   problem.setDebug()
    return problem

  # Make parser for a multi-answer problems
  def mk_parser_problem_ma (self, process_problem_ma):

    (begin, end, ans__, choi__, choi_s__, explain, hint, label, points, prompt, sel, sel_s, title, topics) = self.mk_parser_problem_elements (dex.PROBLEM_MA, Block.PROBLEM_MA)

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
    problem = \
      (begin + \
       title + \
       (label & points & topics) + \
       (hint & prompt) + \
       selects + \
       end) \

    problem.setParseAction(process_problem_ma)
    problem = tokens.set_key_problem(problem)
 #   problem.setDebug()
    return problem

  # Make parser for a multi-choice problems
  def mk_parser_problem_mc (self, process_problem_mc):

    (begin, end, ans__, choi, choi_s, explain, hint, label, points, prompt, sel__, sel_s__, title, topics) = self.mk_parser_problem_elements (dex.PROBLEM_MC, Block.PROBLEM_MC)

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



    problem = \
      (begin + \
       title + \
       (label & points & topics) + \
       (hint & prompt) + \
       choices + \
       end) \

    problem.setParseAction(process_problem_mc)
    problem = tokens.set_key_problem(problem)
#    problem.setDebug()
    return problem


  # Parser for group
  def mk_parser_problem_group (self):
    (begin, end, title, label, parents__) = self.mk_parsers_common (dex.PROBLEM_GROUP, Block.PROBLEM_GROUP)

    # stoppers
    stoppers = com_begin | com_label | com_points | com_prompt |  com_topics | end 
    label = com_label.suppress() + self.mk_parser_text_block (stoppers)
    label = set_text_block_parse_action_single(label)
    label = tokens.set_key_label(label)
    label.setDebug()

    points = com_points.suppress() + self.mk_parser_text_block(stoppers)
    points = set_text_block_parse_action_single(points)
    points = tokens.set_key_points(points)
    points.setDebug()

    topics = com_topics.suppress() + self.mk_parser_text_block (stoppers)
    topics = pp.Optional (topics)
    topics = set_text_block_parse_action(topics)
    topics = tokens.set_key_topics(topics)

    prompt = com_prompt.suppress() + self.mk_parser_text_block (stoppers)
    prompt = pp.Optional(prompt)
    prompt = set_text_block_parse_action(prompt)
    prompt = tokens.set_key_prompt(prompt)

    contents = self.exp_problems
    contents = tokens.set_key_contents(contents)
 #   contents.setDebug()
    group = begin + \
            title + \
            (label & points & topics) + \
            prompt + \
            contents + \
            end
    group.setParseAction(self.process_problem_group)
    group = tokens.set_key_group(group)


    return group

  def mk_blocks (self, block, name):
    name_plural = name + 's'
    blocks = pp.ZeroOrMore(block) 
    blocks = blocks.setName(name_plural).setResultsName(name_plural)
    set_parse_action_list_to_text(blocks)
    return blocks

  def __init__(self, \
               parents_optional, \
               titles_optional, \
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
               process_atom_paragraph_html, \
               process_atom_preamble, \
               process_atom_problem, \
               process_atom_proof, \
               process_atom_proposition, \
               process_atom_remark, \
               process_atom_skip, \
               process_atom_solution, \
               process_atom_syntax, \
               process_atom_teach_ask, \
               process_atom_teach_note, \
               process_atom_theorem, \
               process_answer, \
               process_choice, \
               process_select, \
               process_chapter, \
               process_group, \
               process_problem_fr, \
               process_problem_ma, \
               process_problem_mc, \
               process_problem_group, \
               process_problem_set, \
               process_assignment, \
               process_section, \
               process_subsection, \
               process_subsubsection):

    self.parents_optional = parents_optional
    self.titles_optional = titles_optional

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
    self.process_atom_paragraph_html = process_atom_paragraph_html
    self.process_atom_preamble = process_atom_preamble
    self.process_atom_problem = process_atom_problem
    self.process_atom_proposition = process_atom_proposition
    self.process_atom_proof = process_atom_proof
    self.process_atom_remark = process_atom_remark
    self.process_atom_skip = process_atom_skip
    self.process_atom_solution = process_atom_solution
    self.process_atom_syntax = process_atom_syntax
    self.process_atom_teach_ask = process_atom_teach_ask
    self.process_atom_teach_note = process_atom_teach_note

    self.process_group = process_group
    self.process_chapter = process_chapter
    self.process_problem_fr = process_problem_fr
    self.process_problem_ma = process_problem_ma
    self.process_problem_mc = process_problem_mc
    self.process_problem_group = process_problem_group
    self.process_problem_set = process_problem_set
    self.process_assignment = process_assignment
    self.process_section = process_section
    self.process_subsection = process_subsection
    self.process_subsubsection = process_subsubsection

    # Parser for any begin keyword
    self.begin_any_atom_or_group = self.mk_parser_begin_any_atom_or_group()

    # answers
    self.exp_answer = self.mk_parser_answer(self.process_answer)
    # group this so that it is returned as a list
    self.exp_answers = pp.ZeroOrMore(self.exp_answer)
    self.exp_answers = tokens.set_key_answers(self.exp_answers)
    set_parse_action_list_to_text(self.exp_answers)
#    self.exp_answers.setDebug()

    # choices
    self.exp_choice = self.mk_parser_choice(self.process_choice)
    # group this so that it is returned as a list
    self.exp_choices = pp.OneOrMore(self.exp_choice)
    self.exp_choices = tokens.set_key_choices(self.exp_choices)
    set_parse_action_list_to_text(self.exp_choices)

    # selects
    self.exp_select = self.mk_parser_select(self.process_select)
    # group this so that it is returned as a list
    self.exp_selects = pp.OneOrMore(self.exp_select)
    self.exp_selects = tokens.set_key_selects(self.exp_selects)
    set_parse_action_list_to_text(self.exp_selects)

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
    self.atom_paragraph_html = self.mk_parser_atom(dex.PARAGRAPH_HTML, process_atom_paragraph_html)
    self.atom_preamble = self.mk_parser_atom(dex.PREAMBLE, process_atom_preamble)
    self.atom_problem = self.mk_parser_atom(dex.PROBLEM, process_atom_problem)
    self.atom_proof = self.mk_parser_atom(dex.PROOF,  process_atom_proof)
    self.atom_proposition = self.mk_parser_atom(dex.PROPOSITION,  process_atom_proposition)
    self.atom_remark = self.mk_parser_atom(dex.REMARK, process_atom_remark)
    self.atom_skip = self.mk_parser_atom(dex.SKIP, process_atom_skip)
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
                    self.atom_paragraph_html | \
                    self.atom_problem | \
                    self.atom_proof | \
                    self.atom_proposition | \
                    self.atom_remark | \
                    self.atom_solution | \
                    self.atom_skip | \
                    self.atom_syntax | \
                    self.atom_teach_ask | \
                    self.atom_teach_note | \
                    self.atom_theorem


    # problems
    self.problem_fr = self.mk_parser_problem_fr(process_problem_fr)
    self.problem_ma = self.mk_parser_problem_ma(process_problem_ma)
    self.problem_mc = self.mk_parser_problem_mc(process_problem_mc)


    # dex expression    
    self.exp_atoms = pp.ZeroOrMore(self.exp_atom)
    ## TODO: the next line seems redundant
    self.exp_atoms = self.exp_atoms.ignore(latex_comment)
    self.exp_atoms = self.exp_atoms.setName('exp_atoms').setResultsName('exp_atoms')
    set_parse_action_list_to_text(self.exp_atoms)

    # problems expressions
    self.exp_problem =  self.problem_fr | self.problem_ma | self.problem_mc
    self.exp_problems = pp.ZeroOrMore(self.exp_problem)
    set_parse_action_list_to_text(self.exp_problems)
#    self.exp_problems.setDebug()

    # group expressions
    self.exp_group = self.mk_parser_group()
    self.exp_group = self.exp_group.ignore(latex_comment)

    # problem group expressions
    self.exp_problem_group = self.mk_parser_problem_group()
    self.exp_problem_group = self.exp_problem_group.ignore(latex_comment)

    # problem set elements
    self.exp_problem_set_elements =  self.problem_fr | self.problem_ma | self.problem_mc | self.exp_problem_group
    self.exp_problem_set_elements.setDebug()

    # a subsection element is an atom or a  group
    self.exp_elements = pp.ZeroOrMore(self.exp_atom | self.exp_group)
    # contents is the elements
    set_parse_action_list_to_text(self.exp_elements)
#    self.exp_elements = tokens.set_key_contents(self.exp_elements)

    # problem_set expressions
    self.exp_pset = self.mk_parser_problem_set()

    # dex subsubsection
    self.exp_subsubsection = self.mk_parser_subsubsection()
    self.exp_subsubsection = self.exp_subsubsection.setName('exp_subsubsection').setResultsName('exp_subsubsection')
    self.exp_subsubsections = self.mk_blocks(self.exp_subsubsection, 'exp_subsubsection')

    # dex subsection
    self.exp_subsection = self.mk_parser_subsection()
    self.exp_subsection = self.exp_subsection.setName('exp_subsection').setResultsName('exp_subsection')
    self.exp_subsections = self.mk_blocks (self.exp_subsection, 'exp_subsection') 

    # dex section
    self.exp_section = self.mk_parser_section()
    self.exp_section = self.exp_section.setName('exp_section').setResultsName('exp_section')
    self.exp_sections = self.mk_blocks(self.exp_section, 'exp_section') 

    # dex chapter
    self.exp_chapter = self.mk_parser_chapter()
    self.exp_chapter = self.exp_chapter.setName('exp_chapter').setResultsName('exp_chapter')
    #self.exp_chapter.setDebug()
    self.exp_chapters = self.mk_blocks (self.exp_chapter, 'exp_chapter') 

    self.document = self.exp_chapter + kw_string_end | self.exp_pset + kw_string_end


    # Various modifiers
    self.document = self.document.ignore(latex_comment)
    self.document = self.document.setName('document').setResultsName('document')
  ## END: __init__
## END: class parser

## END Grammar
######################################################################


######################################################################
## BEGIN: parser maker

def mk_uniform_parser (\
                       parents_optional, titles_optional, \
                       process_block_begin, \
                       process_block_end, \
                       process_algo, \
                       process_atom, \
                       process_answer, \
                       process_choice, \
                       process_select, \
                       process_chapter, \
                       process_group, \
                       process_problem_fr, \
                       process_problem_ma, \
                       process_problem_mc, \
                       process_problem_group, \
                       process_problem_set, \
                       process_assignment, \
                       process_section, \
                       process_subsection, process_subsubsection): 

  parser = Parser (\
                        parents_optional, \
                        titles_optional, \
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
                        curry(process_atom, dex.PARAGRAPH_HTML), \
                        curry(process_atom, dex.PREAMBLE), \
                        curry(process_atom, dex.PROBLEM), \
                        curry(process_atom, dex.PROOF), \
                        curry(process_atom, dex.PROPOSITION), \
                        curry(process_atom, dex.REMARK), \
                        curry(process_atom, dex.SKIP), \
                        curry(process_atom, dex.SOLUTION), \
                        curry(process_atom, dex.SYNTAX), \
                        curry(process_atom, dex.TEACH_ASK), \
                        curry(process_atom, dex.TEACH_NOTE), \
                        curry(process_atom, dex.THEOREM), \
                        process_answer, \
                        process_choice, \
                        process_select, \
                        process_chapter, \
                        process_group, \
                        process_problem_fr, \
                        process_problem_ma, \
                        process_problem_mc, \
                        process_problem_group, \
                        process_problem_set, \
                        process_assignment, \
                        process_section, \
                        process_subsection, \
                        process_subsubsection
                     )

  return parser

## END: parser maker
######################################################################

######################################################################
## Begin: Parser function

def parse (parents_optional, titles_optional, \
           process_block_begin, \
           process_block_end, \
           process_algo,  \
           process_atom,  \
           process_answer, \
           process_choice, \
           process_select, \
           process_chapter, \
           process_group, \
           process_problem_fr, process_problem_ma, process_problem_mc, \
           process_problem_group, \
           process_problem_set, \
           process_assignment, \
           process_section, \
           process_subsection, process_subsubsection, \
           data):

  parser = mk_uniform_parser(\
                             parents_optional, titles_optional, \
                             process_block_begin, \
                             process_block_end, \
                             process_algo, \
                             process_atom, \
                             process_answer, \
                             process_choice, \
                             process_select, \
                             process_chapter, \
                             process_group, \
                             process_problem_fr, \
                             process_problem_ma, \
                             process_problem_mc, \
                             process_problem_group, \
                             process_problem_set, \
                             process_assignment, \
                             process_section, \
                             process_subsection, \
                             process_subsubsection)

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
  # elif this_block == Block.PROBLEM_SET:
  #   print ('process_block_begin: this  block is problem_set')
  # elif this_block == Block.SUBSECTION:
  #   print ('process_block_begin: this  block is subsection')
  # elif this_block == Block.ATOM:
  #   print ('process_block_begin: this  block is atom')
  # elif this_block == Block.PROBLEM:
  #   print ('process_block_begin: this  block is problem')
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
  # elif this_block == Block.PROBLEM_SET:
  #   print ('process_block_end: this  block is problem_set')
  # elif this_block == Block.SECTION:
  #   print ('process_block_end: this  block is section')
  # elif this_block == Block.SUBSECTION:
  #   print ('process_block_end: this  block is subsection')
  # elif this_block == Block.ATOM:
  #   print ('process_block_end: this  block is atom')
  # elif this_block == Block.PROBLEM:
  #   print ('process_block_begin: this  block is problem')
  # elif this_block == Block.CHOICE:
  #   print ('process_block_begin: this  block is choice')
  # else :
  #   print 'process_block_end: this  block is UNKNOWN. Fatal ERROR:', this_block

  return toks

def main (infile_name, parents_optional, titles_optional):
  # drop path stuff
  (path, infile_name_file) = os.path.split(infile_name) 
  print 'infile_name:', infile_name_file
  outfile_name = os_utils.mk_file_name_derivative(infile_name_file, os_utils.CORE)

  infile = open(infile_name, 'r')
  outfile = open(outfile_name, 'w')
  data = infile.read ()

  # both labels and numbers are optional
  result = parse (\
             parents_optional, \
             titles_optional, \
             process_block_begin, \
             process_block_end, \
             blocks.algo_to_string, \
             blocks.atom_to_string, \
             blocks.answer_to_string, \
             blocks.choice_to_string, \
             blocks.select_to_string, \
             blocks.chapter_to_string, \
             blocks.group_to_string, \
             blocks.problem_fr_to_string, \
             blocks.problem_ma_to_string, \
             blocks.problem_mc_to_string, \
             blocks.problem_group_to_string, \
             blocks.problem_set_to_string, \
             blocks.assignment_to_string, \
             blocks.section_to_string, \
             blocks.subsection_to_string, \
             blocks.subsubsection_to_string, \
             data)

  # The result consists of a course and a book
  if len(result) == 1:
    problem_set = result[0]
    outfile.write(problem_set + NEWLINE)
    outfile.close()
    print 'Parsed code written into file:', outfile_name
  else:
    course = result[0]
    book = result[1]
    outfile.write(course + NEWLINE + book + NEWLINE)
    outfile.close()
    print 'Parsed code written into file:', outfile_name

  return 0



# if __name__ == '__main__':
#   parents_optional = True
#   titles_optional = True

#   if len(sys.argv) != 2: 
#     print 'Usage: parser inputfile'
#     sys.exit()

#   infile_name = str(sys.argv[1])
#   print 'Executing:', sys.argv[0], infile_name, \
#                       'titles_optional = ', titles_optional,\
#                       'parents_optional = ', parents_optional


#   main (infile_name, parents_optional, titles_optional)



