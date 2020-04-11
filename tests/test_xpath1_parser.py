#!/usr/bin/env python
#
# Copyright (c), 2018-2020, SISSA (International School for Advanced Studies).
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
#
# @author Davide Brunato <brunato@sissa.it>
#
#
# Note: Many tests are built using the examples of the XPath standards,
#       published by W3C under the W3C Document License.
#
#       References:
#           http://www.w3.org/TR/1999/REC-xpath-19991116/
#           http://www.w3.org/TR/2010/REC-xpath20-20101214/
#           http://www.w3.org/TR/2010/REC-xpath-functions-20101214/
#           https://www.w3.org/Consortium/Legal/2015/doc-license
#           https://www.w3.org/TR/charmod-norm/
#
import unittest
import sys
import io
import math
import pickle
from decimal import Decimal
from collections import namedtuple
from xml.etree import ElementTree

try:
    import lxml.etree as lxml_etree
except ImportError:
    lxml_etree = None

from elementpath import *
from elementpath.namespaces import XSD_NAMESPACE, XPATH_FUNCTIONS_NAMESPACE

try:
    from tests import xpath_test_class
except ImportError:
    import xpath_test_class


XML_GENERIC_TEST = """
<root>
    <a id="a_id">
        <b>some content</b>
        <c> space     space    \t .</c></a>
</root>"""

XML_DATA_TEST = """
<values>
   <a>3.4</a>
   <a>20</a>
   <a>-10.1</a>
   <b>alpha</b>
   <c>true</c>
   <d>44</d>
</values>"""


# noinspection PyPropertyAccess,PyTypeChecker
class XPath1ParserTest(xpath_test_class.XPathTestCase):

    def setUp(self):
        self.parser = XPath1Parser(self.namespaces, self.variables, strict=True)
        # self.token = XPath1Parser.symbol_table['(name)'](self.parser, 'test')

    #
    # Test methods
    @unittest.skipIf(sys.version_info < (3,), "Python 2 pickling is not supported.")
    def test_parser_pickling(self):
        if getattr(self.parser, 'schema', None) is None:
            obj = pickle.dumps(self.parser)
            parser = pickle.loads(obj)
            obj = pickle.dumps(self.parser.symbol_table)
            symbol_table = pickle.loads(obj)
            self.assertEqual(self.parser, parser)
            self.assertEqual(self.parser.symbol_table, symbol_table)

    def test_xpath_tokenizer(self):
        # tests from the XPath specification
        self.check_tokenizer("*", ['*'])
        self.check_tokenizer("text()", ['text', '(', ')'])
        self.check_tokenizer("@name", ['@', 'name'])
        self.check_tokenizer("@*", ['@', '*'])
        self.check_tokenizer("para[1]", ['para', '[', '1', ']'])
        self.check_tokenizer("para[last()]", ['para', '[', 'last', '(', ')', ']'])
        self.check_tokenizer("*/para", ['*', '/', 'para'])
        self.check_tokenizer("/doc/chapter[5]/section[2]",
                             ['/', 'doc', '/', 'chapter', '[', '5', ']', '/', 'section',
                              '[', '2', ']'])
        self.check_tokenizer("chapter//para", ['chapter', '//', 'para'])
        self.check_tokenizer("//para", ['//', 'para'])
        self.check_tokenizer("//olist/item", ['//', 'olist', '/', 'item'])
        self.check_tokenizer(".", ['.'])
        self.check_tokenizer(".//para", ['.', '//', 'para'])
        self.check_tokenizer("..", ['..'])
        self.check_tokenizer("../@lang", ['..', '/', '@', 'lang'])
        self.check_tokenizer("chapter[title]", ['chapter', '[', 'title', ']'])
        self.check_tokenizer(
            "employee[@secretary and @assistant]",
            ['employee', '[', '@', 'secretary', '', 'and', '', '@', 'assistant', ']']
        )

        # additional tests from Python XML etree test cases
        self.check_tokenizer("{http://spam}egg", ['{', 'http', ':', '//', 'spam', '}', 'egg'])
        self.check_tokenizer("./spam.egg", ['.', '/', 'spam.egg'])
        self.check_tokenizer(".//spam:egg", ['.', '//', 'spam', ':', 'egg'])

        # additional tests
        self.check_tokenizer("substring-after()", ['substring-after', '(', ')'])
        self.check_tokenizer("contains('XML','XM')", ['contains', '(', "'XML'", ',', "'XM'", ')'])
        self.check_tokenizer(
            "concat('XML', true(), 10)",
            ['concat', '(', "'XML'", ',', '', 'true', '(', ')', ',', '', '10', ')']
        )
        self.check_tokenizer("concat('a', 'b', 'c')",
                             ['concat', '(', "'a'", ',', '', "'b'", ',', '', "'c'", ')'])
        self.check_tokenizer("_last()", ['_last', '(', ')'])
        self.check_tokenizer("last ()", ['last', '', '(', ')'])
        self.check_tokenizer('child::text()', ['child', '::', 'text', '(', ')'])
        self.check_tokenizer('./ /.', ['.', '/', '', '/', '.'])
        self.check_tokenizer('tns :*', ['tns', '', ':', '*'])

    def test_tokens(self):
        # Literals
        self.check_token('(string)', 'literal', "'hello' string",
                         "_string_literal_token(value='hello')", 'hello')
        self.check_token('(integer)', 'literal', "1999 integer",
                         "_integer_literal_token(value=1999)", 1999)
        self.check_token('(float)', 'literal', "3.1415 float",
                         "_float_literal_token(value=3.1415)", 3.1415)
        self.check_token('(decimal)', 'literal', "217.35 decimal",
                         "_decimal_literal_token(value=217.35)", 217.35)
        self.check_token('(name)', 'literal', "'schema' name",
                         "_name_literal_token(value='schema')", 'schema')

        # Variables
        self.check_token('$', 'operator', "$ variable reference",
                         "_DollarSign_operator_token()")

        # Axes
        self.check_token('self', 'axis', "'self' axis", "_self_axis_token()")
        self.check_token('child', 'axis', "'child' axis", "_child_axis_token()")
        self.check_token('parent', 'axis', "'parent' axis", "_parent_axis_token()")
        self.check_token('ancestor', 'axis', "'ancestor' axis", "_ancestor_axis_token()")
        self.check_token('preceding', 'axis', "'preceding' axis", "_preceding_axis_token()")
        self.check_token('descendant-or-self', 'axis', "'descendant-or-self' axis")
        self.check_token('following-sibling', 'axis', "'following-sibling' axis")
        self.check_token('preceding-sibling', 'axis', "'preceding-sibling' axis")
        self.check_token('ancestor-or-self', 'axis', "'ancestor-or-self' axis")
        self.check_token('descendant', 'axis', "'descendant' axis")
        if self.parser.version == '1.0':
            self.check_token('attribute', 'axis', "'attribute' axis")
        self.check_token('following', 'axis', "'following' axis")
        self.check_token('namespace', 'axis', "'namespace' axis")

        # Functions
        self.check_token(
            'position', 'function', "'position' function", "_position_function_token()"
        )

        # Operators
        self.check_token('and', 'operator', "'and' operator", "_and_operator_token()")
        if self.parser.version == '1.0':
            self.check_token(',', 'symbol', "comma symbol", "_Comma_symbol_token()")
        else:
            self.check_token(',', 'operator', "comma operator", "_Comma_operator_token()")

    def test_token_tree(self):
        self.check_tree('child::B1', '(child (B1))')
        self.check_tree('A/B//C/D', '(/ (// (/ (A) (B)) (C)) (D))')
        self.check_tree('child::*/child::B1', '(/ (child (*)) (child (B1)))')
        self.check_tree('attribute::name="Galileo"', "(= (attribute (name)) ('Galileo'))")
        self.check_tree('1 + 2 * 3', '(+ (1) (* (2) (3)))')
        self.check_tree('(1 + 2) * 3', '(* (+ (1) (2)) (3))')
        self.check_tree("false() and true()", '(and (false) (true))')
        self.check_tree("false() or true()", '(or (false) (true))')
        self.check_tree("./A/B[C][D]/E", '(/ (/ (/ (.) (A)) ([ ([ (B) (C)) (D))) (E))')
        self.check_tree("string(xml:lang)", '(string (: (xml) (lang)))')

    def test_token_source(self):
        self.check_source(' child ::B1', 'child::B1')
        self.check_source('false()', 'false()')
        self.check_source("concat('alpha', 'beta', 'gamma')", "concat('alpha', 'beta', 'gamma')")
        self.check_source('1 +2 *  3 ', '1 + 2 * 3')
        self.check_source('(1 + 2) * 3', '(1 + 2) * 3')
        self.check_source(' eg:example ', 'eg:example')
        self.check_source('attribute::name="Galileo"', "attribute::name = 'Galileo'")
        self.check_source(".//eg:a | .//eg:b", '. // eg:a | . // eg:b')
        self.check_source("/A/B[C]", '/ A / B[C]')

        try:
            self.parser.strict = False
            self.check_source("{tns1}name", '{tns1}name')
        finally:
            self.parser.strict = True

    def test_parser_position(self):
        self.assertEqual(self.parser.position, (1, 1))

        try:
            self.assertIsNone(self.parser.parse('false(x)'))
        except SyntaxError as err:
            self.assertIn('line 1, column 7', str(err))

        try:
            self.assertIsNone(self.parser.parse(' false(x)'))
        except SyntaxError as err:
            self.assertIn('line 1, column 8', str(err))

        try:
            self.assertIsNone(self.parser.parse(' false( x)'))
        except SyntaxError as err:
            self.assertIn('line 1, column 9', str(err))

        try:
            self.assertIsNone(self.parser.parse('^'))
        except SyntaxError as err:
            self.assertIn('line 1, column 1', str(err))

        try:
            self.assertIsNone(self.parser.parse(' ^'))
        except SyntaxError as err:
            self.assertIn('line 1, column 2', str(err))

    def test_wrong_syntax(self):
        self.wrong_syntax('')
        self.wrong_syntax("     \n     \n   )")
        self.wrong_syntax('child::1')
        self.wrong_syntax("{}egg")
        self.wrong_syntax("./*:*")
        self.wrong_syntax('./ /.')
        self.wrong_syntax(' eg : example ')

    def test_wrong_nargs(self):
        self.wrong_type("boolean()")       # Too few arguments
        self.wrong_type("count(0, 1, 2)")  # Too many arguments
        self.wrong_type("round(2.5, 1.7)")
        self.wrong_type("contains('XPath', 'XP', 20)")
        self.wrong_type("boolean(1, 5)")

    # XPath expression tests
    def test_node_selection(self):
        self.check_value("mars", [])

        root = self.etree.XML('<A><B1/><B2/><B3/><B2/></A>')
        self.check_value("B1", [root[0]], context=XPathContext(root))
        self.check_value("B2", [root[1], root[3]], context=XPathContext(root))
        self.check_value("B4", [], context=XPathContext(root))

    def test_prefixed_references(self):
        namespaces = {'tst': "http://xpath.test/ns"}
        root = self.etree.XML("""
        <A xmlns:tst="http://xpath.test/ns">
            <tst:B1 b1="beta1"/>
            <tst:B2/>
            <tst:B3 b2="tst:beta2" b3="beta3"/>
            <tst:B2/>
        </A>""")

        # Prefix references
        self.check_tree('eg:unknown', '(: (eg) (unknown))')
        self.check_tree('string(eg:unknown)', '(string (: (eg) (unknown)))')

        # Test evaluate method
        self.check_value("fn:true()", True)
        self.check_value("fx:true()", KeyError)
        self.check_value("tst:B1", [root[0]], context=XPathContext(root))
        self.check_value("tst:B2", [root[1], root[3]], context=XPathContext(root))

        self.check_selector("./tst:B1", root, [root[0]], namespaces=namespaces)
        self.check_selector("./tst:*", root, root[:], namespaces=namespaces)
        self.wrong_syntax("./tst:1")
        self.wrong_syntax("./fn:A")
        self.wrong_syntax("./xs:true()")

        # Namespace wildcard works only for XPath > 1.0
        if self.parser.version == '1.0':
            self.check_selector("./*:B2", root, Exception, namespaces=namespaces)
        else:
            self.check_selector("./*:B2", root, [root[1], root[3]], namespaces=namespaces)

    def test_qname_uri_references(self):
        root = self.etree.XML("""
        <A xmlns:tst="http://xpath.test/ns">
            <tst:B1 b1="beta1"/>
            <tst:B2/>
            <tst:B3 b2="tst:beta2" b3="beta3"/>
            <tst:B2/>
        </A>""")

        self.parser.strict = False
        self.check_tree('{%s}string' % XSD_NAMESPACE,
                        "({ ('http://www.w3.org/2001/XMLSchema') (string))")
        self.check_tree('string({%s}unknown)' % XSD_NAMESPACE,
                        "(string ({ ('http://www.w3.org/2001/XMLSchema') (unknown)))")
        self.wrong_syntax("{%s" % XSD_NAMESPACE)
        self.wrong_syntax("{%s}1" % XSD_NAMESPACE)
        self.wrong_syntax("{%s}alpha" % XPATH_FUNCTIONS_NAMESPACE)

        self.check_value("{%s}true()" % XPATH_FUNCTIONS_NAMESPACE, True)
        self.parser.strict = True
        self.wrong_syntax('{%s}string' % XSD_NAMESPACE)

        if not hasattr(self.etree, 'LxmlError') or self.parser.version > '1.0':
            # Do not test with XPath 1.0 on lxml.
            self.check_selector(
                "./{http://www.w3.org/2001/04/xmlenc#}EncryptedData", root, [], strict=False)
            self.check_selector("./{http://xpath.test/ns}B1", root, [root[0]], strict=False)
            self.check_selector("./{http://xpath.test/ns}*", root, root[:], strict=False)

    def test_node_types(self):
        document = self.etree.parse(io.StringIO(u'<A/>'))
        element = self.etree.Element('schema')
        attribute = 'id', '0212349350'
        namespace = namedtuple('Namespace', 'prefix uri')('xs', 'http://www.w3.org/2001/XMLSchema')
        comment = self.etree.Comment('nothing important')
        pi = self.etree.ProcessingInstruction('action', 'nothing to do')
        text = TextNode('aldebaran')
        context = XPathContext(element)
        self.check_select("node()", [document.getroot()], context=XPathContext(document))
        self.check_selector("node()", element, [])
        context.item = attribute
        self.check_select("self::node()", [attribute], context)
        context.item = namespace
        self.check_select("self::node()", [namespace], context)
        context.item = comment
        self.check_select("self::node()", [comment], context)
        self.check_select("self::comment()", [comment], context)
        context.item = pi
        self.check_select("self::node()", [pi], context)
        self.check_select("self::processing-instruction()", [pi], context)
        context.item = text
        self.check_select("self::node()", [text], context)
        self.check_select("text()", [], context)  # Selects the children
        self.check_selector("node()", self.etree.XML('<author>Dickens</author>'), ['Dickens'])
        self.check_selector("text()", self.etree.XML('<author>Dickens</author>'), ['Dickens'])

        root = self.etree.XML('<author>Dickens</author>')
        if self.etree is not lxml_etree:
            # Skip lxml test because lxml's XPath doesn't include document root
            self.check_selector("//self::node()", root, [root, root, 'Dickens'])
        self.check_selector("//self::text()", root, ['Dickens'])

    def test_node_set_id_function(self):
        # XPath 1.0 id() function: https://www.w3.org/TR/1999/REC-xpath-19991116/#function-id
        root = self.etree.XML('<A><B1 xml:id="foo"/><B2/><B3 xml:id="bar"/><B4 xml:id="baz"/></A>')
        if self.parser.version == '1.0':
            self.check_selector('id("foo")', root, [root[0]])
        else:
            self.check_selector('id("foo")', root, ValueError)

    def test_node_set_functions(self):
        root = self.etree.XML('<A><B1><C1/><C2/></B1><B2/><B3><C3/><C4/><C5/></B3></A>')
        context = XPathContext(root, item=root[1], size=3, position=3)
        self.check_value("position()", 0)
        self.check_value("position()", 4, context=context)
        self.check_value("position()<=2", True)
        self.check_value("position()<=2", False, context=context)
        self.check_value("position()=4", True, context=context)
        self.check_value("position()=3", False, context=context)
        self.check_value("last()", 0)
        self.check_value("last()", 3, context=context)
        self.check_value("last()-1", 2, context=context)

        self.check_selector("name(.)", root, 'A')
        self.check_selector("name(A)", root, '')
        self.check_selector("local-name(A)", root, '')
        self.check_selector("namespace-uri(A)", root, '')
        self.check_selector("name(B2)", root, 'B2')
        self.check_selector("local-name(B2)", root, 'B2')
        self.check_selector("namespace-uri(B2)", root, '')
        if self.parser.version <= '1.0':
            self.check_selector("name(*)", root, 'B1')

        root = self.etree.XML('<tst:A xmlns:tst="http://xpath.test/ns"><tst:B1/></tst:A>')
        self.check_selector("name(.)", root, 'tst:A', namespaces={'tst': "http://xpath.test/ns"})
        self.check_selector("local-name(.)", root, 'A')
        self.check_selector("namespace-uri(.)", root, 'http://xpath.test/ns')
        self.check_selector("name(tst:B1)", root, 'tst:B1',
                            namespaces={'tst': "http://xpath.test/ns"})
        self.check_selector("name(tst:B1)", root, 'tst:B1',
                            namespaces={'tst': "http://xpath.test/ns", '': ''})

    def test_string_function(self):
        self.check_value("string(10.0)", '10.0')
        if self.parser.version == '1.0':
            self.wrong_syntax("string(())")
        else:
            self.check_value("string(())", '')

    def test_string_length_function(self):
        root = self.etree.XML(XML_GENERIC_TEST)

        self.check_value("string-length('hello world')", 11)
        self.check_value("string-length('')", 0)
        self.check_selector("a[string-length(@id) = 4]", root, [root[0]])
        self.check_selector("a[string-length(@id) = 3]", root, [])
        self.check_selector("//b[string-length(.) = 12]", root, [root[0][0]])
        self.check_selector("//b[string-length(.) = 10]", root, [])
        self.check_selector("//none[string-length(.) = 10]", root, [])
        self.check_value('fn:string-length("Harp not on that string, madam; that is past.")', 45)

        if self.parser.version == '1.0':
            self.wrong_syntax("string-length(())")
            self.check_value("string-length(12345)", 5)
        else:
            self.check_value("string-length(())", 0)
            self.check_value("string-length(('alpha'))", 5)
            self.check_value("string-length(('alpha'))", 5)
            self.wrong_type("string-length(12345)")
            self.wrong_type("string-length(('12345', 'abc'))")
            self.parser.compatibility_mode = True
            self.check_value("string-length(('12345', 'abc'))", 5)
            self.check_value("string-length(12345)", 5)
            self.parser.compatibility_mode = False

    def test_normalize_space_function(self):
        root = self.etree.XML(XML_GENERIC_TEST)

        self.check_value("normalize-space('  hello  \t  world ')", 'hello world')
        self.check_selector("//c[normalize-space(.) = 'space space .']", root, [root[0][1]])
        self.check_value('fn:normalize-space(" The  wealthy curled darlings of   our  nation. ")',
                         'The wealthy curled darlings of our nation.')
        if self.parser.version == '1.0':
            self.wrong_syntax('fn:normalize-space(())')
            self.check_value("normalize-space(1000)", '1000')
            self.check_value("normalize-space(true())", 'True')
        else:
            self.check_value('fn:normalize-space(())', '')
            self.wrong_type("normalize-space(true())")
            self.wrong_type("normalize-space(('\ta  b c  ', 'other'))")
            self.parser.compatibility_mode = True
            self.check_value("normalize-space(true())", 'True')
            self.check_value("normalize-space(('\ta  b\tc  ', 'other'))", 'a b c')
            self.parser.compatibility_mode = False

    def test_translate_function(self):
        root = self.etree.XML(XML_GENERIC_TEST)

        self.check_value("translate('hello world!', 'hw', 'HW')", 'Hello World!')
        self.check_value("translate('hello world!', 'hwx', 'HW')", 'Hello World!')
        self.check_value("translate('hello world!', 'hw!', 'HW')", 'Hello World')
        self.check_selector("a[translate(@id, 'id', 'no') = 'a_no']", root, [root[0]])
        self.check_selector("a[translate(@id, 'id', 'na') = 'a_no']", root, [])
        self.check_selector(
            "//b[translate(., 'some', 'one2') = 'one2 cnnt2nt']", root, [root[0][0]])
        self.check_selector("//b[translate(., 'some', 'two2') = 'one2 cnnt2nt']", root, [])
        self.check_selector("//none[translate(., 'some', 'two2') = 'one2 cnnt2nt']", root, [])

        self.check_value('fn:translate("bar","abc","ABC")', 'BAr')
        self.check_value('fn:translate("--aaa--","abc-","ABC")', 'AAA')
        self.check_value('fn:translate("abcdabc", "abc", "AB")', "ABdAB")

        if self.parser.version > '1.0':
            self.check_value("translate((), 'hw', 'HW')", '')

    def test_variable_substitution(self):
        root = self.etree.XML('<ups-units>'
                              '  <unit><power>40kW</power></unit>'
                              '  <unit><power>20kW</power></unit>'
                              '  <unit><power>30kW</power><model>XYZ</model></unit>'
                              '</ups-units>')
        variables = {'ups1': root[0], 'ups2': root[1], 'ups3': root[2]}
        self.check_selector('string($ups1/power)', root, '40kW', variables=variables)

        self.check_value('$word', 'alpha')
        self.wrong_syntax('$eg:word', 'variable reference requires a simple reference name')
        self.wrong_syntax('${http://xpath.test/ns}word',
                          "unexpected symbol '{' after $ variable reference")

    def test_substring_function(self):
        root = self.etree.XML(XML_GENERIC_TEST)

        self.check_value("substring('Preem Palver', 1)", 'Preem Palver')
        self.check_value("substring('Preem Palver', 2)", 'reem Palver')
        self.check_value("substring('Preem Palver', 7)", 'Palver')
        self.check_value("substring('Preem Palver', 1, 5)", 'Preem')
        self.wrong_type("substring('Preem Palver', 'c', 5)")
        self.wrong_type("substring('Preem Palver', 1, '5')")
        self.check_selector("a[substring(@id, 1) = 'a_id']", root, [root[0]])
        self.check_selector("a[substring(@id, 2) = '_id']", root, [root[0]])
        self.check_selector("a[substring(@id, 3) = '_id']", root, [])
        self.check_selector("//b[substring(., 1, 5) = 'some ']", root, [root[0][0]])
        self.check_selector("//b[substring(., 1, 6) = 'some ']", root, [])
        self.check_selector("//none[substring(., 1, 6) = 'some ']", root, [])
        self.check_value("substring('12345', 1.5, 2.6)", '234')
        self.check_value("substring('12345', 0, 3)", '12')

        if self.parser.version == '1.0':
            self.check_value("substring('12345', 0 div 0, 3)", '')
            self.check_value("substring('12345', 1, 0 div 0)", '')
            self.check_value("substring('12345', -42, 1 div 0)", '12345')
            self.check_value("substring('12345', -1 div 0, 1 div 0)", '')
        else:
            self.check_value('fn:substring("motor car", 6)', ' car')
            self.check_value('fn:substring("metadata", 4, 3)', 'ada')
            self.check_value('fn:substring("12345", 1.5, 2.6)', '234')
            self.check_value('fn:substring("12345", 0, 3)', '12')
            self.check_value('fn:substring("12345", 5, -3)', '')
            self.check_value('fn:substring("12345", -3, 5)', '1')
            self.check_value('fn:substring("12345", 0 div 0E0, 3)', '')
            self.check_value('fn:substring("12345", 1, 0 div 0E0)', '')
            self.check_value('fn:substring((), 1, 3)', '')
            self.check_value('fn:substring("12345", -42, 1 div 0E0)', '12345')
            self.check_value('fn:substring("12345", -1 div 0E0, 1 div 0E0)', '')

            self.check_value('fn:substring(("alpha"), 1, 3)', 'alp')
            self.check_value('fn:substring(("alpha"), (1), 3)', 'alp')
            self.check_value('fn:substring(("alpha"), 1, (3))', 'alp')
            self.wrong_type('fn:substring(("alpha"), (1, 2), 3)')
            self.wrong_type('fn:substring(("alpha", "beta"), 1, 3)')
            self.parser.compatibility_mode = True
            self.check_value('fn:substring(("alpha", "beta"), 1, 3)', 'alp')
            self.parser.compatibility_mode = False

    def test_starts_with_function(self):
        root = self.etree.XML(XML_GENERIC_TEST)

        self.check_value("starts-with('Hello World', 'Hello')", True)
        self.check_value("starts-with('Hello World', 'hello')", False)

        self.check_selector("a[starts-with(@id, 'a_i')]", root, [root[0]])
        self.check_selector("a[starts-with(@id, 'a_b')]", root, [])
        self.check_selector("//b[starts-with(., 'some')]", root, [root[0][0]])
        self.check_selector("//b[starts-with(., 'none')]", root, [])
        self.check_selector("//none[starts-with(., 'none')]", root, [])

        self.check_selector("a[starts-with(@id, 'a_id')]", root, [root[0]])
        self.check_selector("a[starts-with(@id, 'a')]", root, [root[0]])
        self.check_selector("a[starts-with(@id, 'a!')]", root, [])
        self.check_selector("//b[starts-with(., 'some')]", root, [root[0][0]])
        self.check_selector("//b[starts-with(., 'a')]", root, [])

        self.check_value("starts-with('', '')", True)

        self.check_value('fn:starts-with("abracadabra", "abra")', True)
        self.check_value('fn:starts-with("abracadabra", "a")', True)
        self.check_value('fn:starts-with("abracadabra", "bra")', False)

        if self.parser.version == '1.0':
            self.wrong_syntax("starts-with((), ())")
            self.check_value("starts-with('1999', 19)", True)
        else:
            self.check_value('fn:starts-with("tattoo", "tat")', True)
            self.check_value('fn:starts-with ( "tattoo", "att")', False)
            self.check_value('fn:starts-with ((), ())', True)
            self.wrong_type("starts-with('1999', 19)")
            self.parser.compatibility_mode = True
            self.check_value("starts-with('1999', 19)", True)
            self.parser.compatibility_mode = False

    def test_concat_function(self):
        root = self.etree.XML(XML_GENERIC_TEST)

        self.check_value("concat('alpha', 'beta', 'gamma')", 'alphabetagamma')
        self.check_value("concat('', '', '')", '')
        self.check_value("concat('alpha', 10, 'gamma')", 'alpha10gamma')

        self.check_value("concat('alpha', 'beta', 'gamma')", 'alphabetagamma')
        self.check_value("concat('alpha', 10, 'gamma')", 'alpha10gamma')
        self.check_value("concat('alpha', 'gamma')", 'alphagamma')
        self.check_selector("a[concat(@id, '_foo') = 'a_id_foo']", root, [root[0]])
        self.check_selector("a[concat(@id, '_fo') = 'a_id_foo']", root, [])
        self.check_selector("//b[concat(., '_foo') = 'some content_foo']", root, [root[0][0]])
        self.check_selector("//b[concat(., '_fo') = 'some content_foo']", root, [])
        self.check_selector("//none[concat(., '_fo') = 'some content_foo']", root, [])
        self.wrong_syntax("concat()")

        self.wrong_syntax("concat()")
        if self.parser.version == '1.0':
            self.wrong_syntax("concat((), (), ())")
        else:
            self.check_value("concat((), (), ())", '')
            self.check_value("concat(('a'), (), ('c'))", 'ac')
            self.wrong_type("concat(('a', 'b'), (), ('c'))")
            self.parser.compatibility_mode = True
            self.check_value("concat(('a', 'b'), (), ('c'))", 'ac')
            self.parser.compatibility_mode = False

    def test_contains_function(self):
        root = self.etree.XML(XML_GENERIC_TEST)

        self.check_value("contains('XPath','XP')", True)
        self.check_value("contains('XP','XPath')", False)
        self.check_value("contains('', '')", True)

        self.check_selector("a[contains(@id, '_i')]", root, [root[0]])
        self.check_selector("a[contains(@id, '_b')]", root, [])
        self.check_selector("//b[contains(., 'c')]", root, [root[0][0]])
        self.check_selector("//b[contains(., ' -con')]", root, [])
        self.check_selector("//none[contains(., ' -con')]", root, [])

        if self.parser.version == '1.0':
            self.wrong_syntax("contains((), ())")
            self.check_value("contains('XPath', 20)", False)
        else:
            self.check_value('fn:contains ( "tattoo", "t")', True)
            self.check_value('fn:contains ( "tattoo", "ttt")', False)
            self.check_value('fn:contains ( "", ())', True)
            self.wrong_type("contains('XPath', 20)")
            self.parser.compatibility_mode = True
            self.check_value("contains('XPath', 20)", False)
            self.parser.compatibility_mode = False

    def test_substring_before_function(self):
        root = self.etree.XML(XML_GENERIC_TEST)

        self.check_value("substring-before('Wolfgang Amadeus Mozart', 'Wolfgang')", '')
        self.check_value("substring-before('Wolfgang Amadeus Mozart', 'Amadeus')", 'Wolfgang ')
        self.check_value('substring-before("1999/04/01","/")', '1999')

        self.check_selector("a[substring-before(@id, 'a') = '']", root, [root[0]])
        self.check_selector("a[substring-before(@id, 'id') = 'a_']", root, [root[0]])
        self.check_selector("a[substring-before(@id, 'id') = '']", root, [])
        self.check_selector("//b[substring-before(., ' ') = 'some']", root, [root[0][0]])
        self.check_selector("//b[substring-before(., 'con') = 'some']", root, [])
        self.check_selector("//none[substring-before(., 'con') = 'some']", root, [])

        if self.parser.version == '1.0':
            self.check_value("substring-before('2017-10-27', 10)", '2017-')
            self.wrong_syntax("fn:substring-before((), ())")
        else:
            self.check_value('fn:substring-before ( "tattoo", "attoo")', 't')
            self.check_value('fn:substring-before ( "tattoo", "tatto")', '')
            self.check_value('fn:substring-before ((), ())', '')
            self.wrong_type("substring-before('2017-10-27', 10)")
            self.parser.compatibility_mode = True
            self.check_value("substring-before('2017-10-27', 10)", '2017-')
            self.parser.compatibility_mode = False

    def test_substring_after_function(self):
        root = self.etree.XML(XML_GENERIC_TEST)

        self.check_value("substring-after('Wolfgang Amadeus Mozart', 'Amadeus ')", 'Mozart')
        self.check_value("substring-after('Wolfgang Amadeus Mozart', 'Mozart')", '')
        self.check_value("substring-after('', '')", '')
        self.check_value("substring-after('Mozart', 'B')", '')
        self.check_value("substring-after('Mozart', 'Bach')", '')
        self.check_value("substring-after('Mozart', 'Amadeus')", '')
        self.check_value("substring-after('Mozart', '')", 'Mozart')
        self.check_value('substring-after("1999/04/01","/")', '04/01')
        self.check_value('substring-after("1999/04/01","19")', '99/04/01')

        self.check_value("substring-after('Wolfgang Amadeus Mozart', 'Amadeus ')", 'Mozart')
        self.check_value("substring-after('Wolfgang Amadeus Mozart', 'Mozart')", '')
        self.check_selector("a[substring-after(@id, 'a') = '_id']", root, [root[0]])
        self.check_selector("a[substring-after(@id, 'id') = '']", root, [root[0]])
        self.check_selector("a[substring-after(@id, 'i') = '']", root, [])
        self.check_selector("//b[substring-after(., ' ') = 'content']", root, [root[0][0]])
        self.check_selector("//b[substring-after(., 'con') = 'content']", root, [])
        self.check_selector("//none[substring-after(., 'con') = 'content']", root, [])

        if self.parser.version == '1.0':
            self.wrong_syntax("fn:substring-after((), ())")
        else:
            self.check_value('fn:substring-after("tattoo", "tat")', 'too')
            self.check_value('fn:substring-after("tattoo", "tattoo")', '')
            self.check_value("fn:substring-after((), ())", '')
            self.wrong_type("substring-after('2017-10-27', 10)")
            self.parser.compatibility_mode = True
            self.check_value("substring-after('2017-10-27', 10)", '-27')
            self.parser.compatibility_mode = False

    def test_boolean_functions(self):
        self.check_value("true()", True)
        self.check_value("false()", False)
        self.check_value("not(false())", True)
        self.check_value("not(true())", False)
        self.check_value("boolean(0)", False)
        self.check_value("boolean(1)", True)
        self.check_value("boolean(-1)", True)
        self.check_value("boolean('hello!')", True)
        self.check_value("boolean('   ')", True)
        self.check_value("boolean('')", False)

        if self.parser.version == '1.0':
            self.wrong_syntax("boolean(())")
        else:
            self.check_value("boolean(())", False)

    def test_lang_function(self):
        # From https://www.w3.org/TR/1999/REC-xpath-19991116/#section-Boolean-Functions
        self.check_selector('lang("en")', self.etree.XML('<para xml:lang="en"/>'), True)
        self.check_selector('lang("en")', self.etree.XML('<div xml:lang="en"><para/></div>'), True)
        self.check_selector('lang("en")', self.etree.XML('<para xml:lang="EN"/>'), True)
        self.check_selector('lang("en")', self.etree.XML('<para xml:lang="en-us"/>'), True)
        self.check_selector('lang("en")', self.etree.XML('<para xml:lang="it"/>'), False)

    def test_logical_and_operator(self):
        self.check_value("false() and true()", False)
        self.check_value("true() and true()", True)
        self.check_value("1 and 0", False)
        self.check_value("1 and 1", True)
        self.check_value("1 and 'jupiter'", True)
        self.check_value("0 and 'mars'", False)
        self.check_value("1 and mars", False)

    def test_logical_or_operator(self):
        self.check_value("false() or true()", True)
        self.check_value("true() or false()", True)

    def test_logical_expressions(self):
        root_token = self.parser.parse("(@a and not(@b)) or (not(@a) and @b)")
        context = XPathContext(self.etree.XML('<root a="10" b="0"/>'))
        self.assertTrue(root_token.evaluate(context=context) is False)
        context = XPathContext(self.etree.XML('<root a="10" b="1"/>'))
        self.assertTrue(root_token.evaluate(context=context) is False)
        context = XPathContext(self.etree.XML('<root a="10"/>'))
        self.assertTrue(root_token.evaluate(context=context) is True)
        context = XPathContext(self.etree.XML('<root a="0"/>'))
        self.assertTrue(root_token.evaluate(context=context) is True)
        context = XPathContext(self.etree.XML('<root b="0"/>'))
        self.assertTrue(root_token.evaluate(context=context) is True)
        context = XPathContext(self.etree.XML('<root/>'))
        self.assertTrue(root_token.evaluate(context=context) is False)

    def test_comparison_operators(self):
        self.check_value("0.05 = 0.05", True)
        self.check_value("19.03 != 19.02999", True)
        self.check_value("-1.0 = 1.0", False)
        self.check_value("1 <= 2", True)
        self.check_value("5 >= 9", False)
        self.check_value("5 > 3", True)
        self.check_value("5 < 20.0", True)
        self.check_value("false() = 1", False)
        self.check_value("0 = false()", True)
        self.check_value("2 * 2 = 4", True)

    def test_comparison_of_sequences(self):
        root = self.etree.XML('<table>'
                              '    <unit id="1"><cost>50</cost></unit>'
                              '    <unit id="2"><cost>30</cost></unit>'
                              '    <unit id="3"><cost>20</cost></unit>'
                              '    <unit id="2"><cost>40</cost></unit>'
                              '</table>')
        self.check_selector("/table/unit[2]/cost <= /table/unit[1]/cost", root, True)
        self.check_selector("/table/unit[2]/cost > /table/unit[position()!=2]/cost", root, True)
        self.check_selector("/table/unit[3]/cost > /table/unit[position()!=3]/cost", root, False)

        self.check_selector(". = 'Dickens'", self.etree.XML('<author>Dickens</author>'), True)

    def test_numerical_expressions(self):
        self.check_value("9", 9)
        self.check_value("-3", -3)
        self.check_value("7.1", Decimal('7.1'))
        self.check_value("0.45e3", 0.45e3)
        self.check_value(" 7+5 ", 12)
        self.check_value("8 - 5", 3)
        self.check_value("-8 - 5", -13)
        self.check_value("-3 * 7", -21)
        self.check_value("9 - 1 + 6", 14)
        self.check_value("(5 * 7) + 9", 44)
        self.check_value("-3 * 7", -21)

    def test_div_operator(self):
        self.check_value("5 div 2", 2.5)
        self.check_value("0 div 2", 0.0)
        if self.parser.version > '1.0':
            self.check_value("() div 2")

    def test_numerical_add_operator(self):
        self.check_value("3 + 8", 11)
        self.check_value("+9", 9)
        self.wrong_syntax("+")

        root = self.etree.XML(XML_DATA_TEST)
        if self.parser.version == '1.0':
            self.check_value("'9' + 5.0", 14)
            self.check_selector("/values/a + 2", root, 5.4)
            self.check_value("/values/b + 2", float('nan'), context=XPathContext(root))
            self.check_value("+'alpha'", float('nan'))
            self.check_value("3 + 'alpha'", float('nan'))
        else:
            self.check_selector("/values/a + 2", root, TypeError)
            self.check_value("/values/b + 2", TypeError, context=XPathContext(root))
            self.wrong_type("+'alpha'")
            self.wrong_type("3 + 'alpha'")

        self.check_selector("/values/d + 3", root, 47)

    def test_numerical_sub_operator(self):
        self.check_value("9 - 5.0", 4)
        self.check_value("-8", -8)
        self.wrong_syntax("-")

        root = self.etree.XML(XML_DATA_TEST)
        if self.parser.version == '1.0':
            self.check_value("'9' - 5.0", 4)
            self.check_selector("/values/a - 2", root, 1.4)
            self.check_value("/values/b - 1", float('nan'), context=XPathContext(root))
            self.check_value("-'alpha'", float('nan'))
            self.check_value("3 - 'alpha'", float('nan'))
        else:
            self.check_selector("/values/a - 2", root, TypeError)
            self.check_value("/values/b - 2", TypeError, context=XPathContext(root))
            self.wrong_type("-'alpha'")
            self.wrong_type("3 - 'alpha'")

        self.check_selector("/values/d - 3", root, 41)

    def test_numerical_mod_operator(self):
        self.check_value("11 mod 3", 2)
        self.check_value("4.5 mod 1.2", Decimal('0.9'))
        self.check_value("1.23E2 mod 0.6E1", 3.0E0)

        root = self.etree.XML(XML_DATA_TEST)
        if self.parser.version == '1.0':
            self.check_selector("/values/a mod 2", root, 1.4)
            self.check_value("/values/b mod 2", float('nan'), context=XPathContext(root))
        else:
            self.check_selector("/values/a mod 2", root, TypeError)
            self.check_value("/values/b mod 2", TypeError, context=XPathContext(root))

        self.check_selector("/values/d mod 3", root, 2)

    def test_number_function(self):
        root = self.etree.XML('<root>15</root>')

        self.check_value("number()", MissingContextError)
        self.check_value("number()", 15, context=XPathContext(root))
        self.check_value("number()", 15, context=XPathContext(root, item=root.text))
        self.check_value("number(.)", 15, context=XPathContext(root))
        self.check_value("number(5.0)", 5.0)
        self.check_value("number('text')", math.isnan)
        self.check_value("number('-11')", -11)
        self.check_selector("number(9)", root, 9.0)

        if self.parser.version == '1.0':
            self.wrong_syntax("number(())")
        else:
            self.check_value("number(())", float('nan'), context=XPathContext(root))

            root = self.etree.XML(XML_DATA_TEST)
            self.check_selector("/values/a/number()", root, [3.4, 20.0, -10.1])
            results = select(root, "/values/*/number()", parser=self.parser.__class__)
            self.assertEqual(results[:3], [3.4, 20.0, -10.1])
            self.assertTrue(math.isnan(results[3]) and math.isnan(results[4]))
            self.check_selector("number(/values/d)", root, 44.0)
            self.check_selector("number(/values/a)", root, TypeError)

    def test_count_function(self):
        root = self.etree.XML('<A><B><C/><C/></B><B/><B><C/><C/><C/></B></A>')
        self.check_selector("count(B)", root, 3)
        self.check_selector("count(.//C)", root, 5)

        root = self.etree.XML('<value max="10" min="0">5</value>')
        self.check_selector("count(@avg)", root, 0)
        self.check_selector("count(@max)", root, 1)
        self.check_selector("count(@min)", root, 1)
        self.check_selector("count(@min | @max)", root, 2)
        self.check_selector("count(@min | @avg)", root, 1)
        self.check_selector("count(@top | @avg)", root, 0)
        self.check_selector("count(@min | @max) = 1", root, False)
        self.check_selector("count(@min | @max) = 2", root, True)

    def test_sum_function(self):
        root = self.etree.XML(XML_DATA_TEST)
        self.check_value("sum($values)", 35)
        if self.parser.version == '1.0':
            self.wrong_syntax("sum(())")
        else:
            self.check_value("sum(())", 0)
            self.check_value("sum((), ())", [])
            self.check_selector("sum(/values/a)", root, 13.299999999999999)
            self.check_selector("sum(/values/*)", root, float('nan'))

    def test_ceiling_function(self):
        root = self.etree.XML(XML_DATA_TEST)
        self.check_value("ceiling(10.5)", 11)
        self.check_value("ceiling(-10.5)", -10)
        self.check_selector("//a[ceiling(.) = 10]", root, [])
        self.check_selector("//a[ceiling(.) = -10]", root, [root[2]])
        if self.parser.version == '1.0':
            self.wrong_syntax("ceiling(())")
        else:
            self.check_value("ceiling(())", [])
            self.check_value("ceiling((10.5))", 11)
            self.wrong_type("ceiling((10.5, 17.3))")

    def test_floor_function(self):
        root = self.etree.XML(XML_DATA_TEST)
        self.check_value("floor(10.5)", 10)
        self.check_value("floor(-10.5)", -11)
        self.check_selector("//a[floor(.) = 10]", root, [])
        self.check_selector("//a[floor(.) = 20]", root, [root[1]])

        if self.parser.version == '1.0':
            self.wrong_syntax("floor(())")
            self.check_selector("//ab[floor(.) = 10]", root, [])
        else:
            self.check_value("floor(())", [])
            self.check_value("floor((10.5))", 10)
            self.wrong_type("floor((10.5, 17.3))")

    def test_round_function(self):
        self.check_value("round(2.5)", 3)
        self.check_value("round(2.4999)", 2)
        self.check_value("round(-2.5)", -2)
        if self.parser.version == '1.0':
            self.wrong_syntax("round(())")
        else:
            self.check_value("round(())", [])
            self.check_value("round((10.5))", 11)
            self.wrong_type("round((2.5, 12.2))")

    def test_context_variables(self):
        root = self.etree.XML('<A><B1><C/></B1><B2/><B3><C1/><C2/></B3></A>')
        context = XPathContext(root, variables={'alpha': 10, 'id': '19273222'})
        self.check_value("$alpha", None)  # Do not raise if the dynamic context is None
        self.check_value("$alpha", 10, context=context)
        self.check_value("$beta", NameError, context=context)
        self.check_value("$id", '19273222', context=context)
        self.wrong_syntax("$id()")

    def test_path_step_operator(self):
        root = self.etree.XML('<A><B1><C1/></B1><B2/><B3><C1/><C2/></B3></A>')
        document = self.etree.ElementTree(root)

        self.check_selector('/', root, [])
        if self.etree is ElementTree or self.parser.version > '1.0':
            # Skip lxml'xpath() comparison because it doesn't include document selection
            self.check_selector('/', document, [document])

        self.check_selector('/B1', root, [])
        self.check_selector('/A1', root, [])
        self.check_selector('/A', root, [root])
        self.check_selector('/A/B1', root, [root[0]])
        self.check_selector('/A/*', root, [root[0], root[1], root[2]])
        self.check_selector('/*/*', root, [root[0], root[1], root[2]])
        self.check_selector('/A/B1/C1', root, [root[0][0]])
        self.check_selector('/A/B1/*', root, [root[0][0]])
        self.check_selector('/A/B3/*', root, [root[2][0], root[2][1]])
        self.check_selector('child::*/child::C1', root, [root[0][0], root[2][0]])
        self.check_selector('/A/child::B3', root, [root[2]])
        self.check_selector('/A/child::C1', root, [])

        if self.parser.version == '1.0':
            self.wrong_syntax('/true()')
            self.wrong_syntax('/A/true()')
            self.wrong_syntax('/|')
        else:
            self.check_value('/true()', [True], context=XPathContext(root))
            self.check_value('/A/true()', [True], context=XPathContext(root))
            self.wrong_syntax('/|')

        root = self.etree.XML("<A><B><C><D><E/></D></C></B></A>")
        context = XPathContext(root)
        self.check_value('/A', [root], context=context)

        context = XPathContext(root, item=root[0][0])
        self.check_value('/A', [], context=context)

    def test_context_item_expression(self):
        root = self.etree.XML('<A><B1><C/></B1><B2/><B3><C1/><C2/></B3></A>')
        self.check_selector('.', root, [root])
        self.check_selector('./.', root, [root])
        self.check_selector('././.', root, [root])
        self.check_selector('./././.', root, [root])
        self.check_selector('/', root, [])
        self.check_selector('/.', root, [])
        self.check_selector('/./.', root, [])
        self.check_selector('/././.', root, [])
        self.check_selector('/A/.', root, [root])
        self.check_selector('/A/B1/.', root, [root[0]])
        self.check_selector('/A/B1/././.', root, [root[0]])
        self.check_selector('1/.', root, TypeError)

        document = self.etree.ElementTree(root)
        self.check_value('.', [root], context=XPathContext(root))
        self.check_value('.', [document], context=XPathContext(root=document))

    def test_self_axis(self):
        root = self.etree.XML('<A>A text<B1>B1 text</B1><B2/><B3>B3 text</B3></A>')
        self.check_selector('self::node()', root, [root])
        self.check_selector('self::text()', root, [])

    def test_child_axis(self):
        root = self.etree.XML('<A>A text<B1>B1 text</B1><B2/><B3>B3 text</B3></A>')
        self.check_selector('child::B1', root, [root[0]])
        self.check_selector('child::A', root, [])
        self.check_selector('child::text()', root, ['A text'])
        self.check_selector('child::node()', root, ['A text'] + root[:])
        self.check_selector('child::*', root, root[:])

        root = self.etree.XML('<A xmlns:ns="http://www.example.com/ns/"><ns:B1/><B2/></A>')
        self.check_selector('child::eg:A', root, [],
                            namespaces={'eg': 'http://www.example.com/ns/'})
        self.check_selector('child::eg:B1', root, [root[0]],
                            namespaces={'eg': 'http://www.example.com/ns/'})

    def test_descendant_axis(self):
        root = self.etree.XML('<A><B1><C/></B1><B2/><B3><C1/><C2/></B3></A>')
        self.check_selector('descendant::node()', root, [e for e in root.iter()][1:])
        self.check_selector('/descendant::node()', root, [e for e in root.iter()])

    def test_descendant_or_self_axis(self):
        root = self.etree.XML('<A><B1><C/></B1><B2/><B3><C/><C1/></B3></A>')
        self.check_selector('descendant-or-self::node()', root, [e for e in root.iter()])
        self.check_selector('descendant-or-self::node()/.', root, [e for e in root.iter()])

    def test_double_slash_shortcut(self):
        root = self.etree.XML('<A><B1><C/></B1><B2/><B3><C/><C1/></B3></A>')
        self.check_selector('//.', root, [e for e in root.iter()])
        self.check_selector('/A//.', root, [e for e in root.iter()])
        self.check_selector('/A//self::node()', root, [e for e in root.iter()])
        self.check_selector('//C1', root, [root[2][1]])
        self.check_selector('//B2', root, [root[1]])
        self.check_selector('//C', root, [root[0][0], root[2][0]])
        self.check_selector('//*', root, [e for e in root.iter()])

        self.check_value('/1//*', TypeError, context=XPathContext(root))

        # Issue #14
        root = self.etree.XML("""
        <pm>
            <content>
                <pmEntry>
                    <pmEntry pmEntryType="pm001">
                    </pmEntry>
                </pmEntry>
            </content>
        </pm>""")

        self.check_selector('/pm/content/pmEntry/pmEntry//pmEntry[@pmEntryType]', root, [])

        root = self.etree.XML("<A><B><C><D><E/></D></C></B></A>")
        context = XPathContext(root)
        self.check_value('//*', list(root.iter()), context=context)

        context = XPathContext(root, item=root[0][0])
        self.check_value('//*', [], context=context)

    def test_double_slash_shortcut_pr16(self):
        # Pull-Request #16
        root = self.etree.XML("""
        <html>
            <ul>
                <li>
                    <span class='class_a'>a</span>
                </li>
            </ul>
        </html>""")

        self.check_selector("//span", root, [root[0][0][0]])
        # self.check_selector("//span[concat('', '', 'class_a')='class_a']/text()", root, ['a'])
        self.check_selector("//span[concat('', '', @class)='class_a']/text()", root, ['a'])

    def test_following_axis(self):
        root = self.etree.XML(
            '<A><B1><C1/></B1><B2/><B3><C1/><C2/></B3><B4><C1><D1/></C1></B4></A>')
        self.check_selector('/A/B1/C1/following::*', root, [
            root[1], root[2], root[2][0], root[2][1], root[3], root[3][0], root[3][0][0]
        ])
        self.check_selector('/A/B1/following::C1', root, [root[2][0], root[3][0]])

    def test_following_sibling_axis(self):
        root = self.etree.XML('<A><B1><C1 a="1"/><C2/><C3/></B1><B2><C1/><C2/><C3/><C4/></B2></A>')
        self.check_selector(
            '/A/B1/C1/following-sibling::*', root, [root[0][1], root[0][2]])
        self.check_selector(
            '/A/B2/C1/following-sibling::*', root, [root[1][1], root[1][2], root[1][3]])
        self.check_selector('/A/B1/C1/following-sibling::C3', root, [root[0][2]])

        self.check_selector("/A/B1/C1/1/following-sibling::*", root, TypeError)
        self.check_selector("/A/B1/C1/@a/following-sibling::*", root, [])

    def test_attribute_abbreviation_and_axis(self):
        root = self.etree.XML('<A id="1" a="alpha">'
                              '<B1 b1="beta1"/><B2/><B3 b2="beta2" b3="beta3"/></A>')
        self.check_selector('/A/B1/attribute::*', root, ['beta1'])
        self.check_selector('/A/B1/@*', root, ['beta1'])
        self.check_selector('/A/B3/attribute::*', root, {'beta2', 'beta3'})
        self.check_selector('/A/attribute::*', root, {'1', 'alpha'})

        root = self.etree.XML('<value choice="int">10</value>')
        self.check_selector('@choice', root, ['int'])
        root = self.etree.XML('<ns:value xmlns:ns="ns" choice="int">10</ns:value>')
        self.check_selector('@choice', root, ['int'])
        self.check_selector('@choice="int"', root, True)
        self.check_value('@choice', MissingContextError)
        self.check_value('@1', SyntaxError, context=XPathContext(root))

    def test_namespace_axis(self):
        root = self.etree.XML('<A xmlns:tst="http://xpath.test/ns"><tst:B1/></A>')
        namespaces = list(self.parser.DEFAULT_NAMESPACES.items()) \
            + [('tst', 'http://xpath.test/ns')]
        self.check_selector('/A/namespace::*', root, expected=set(namespaces),
                            namespaces=namespaces[-1:])

        if self.etree is lxml_etree:
            self.check_selector('/A/namespace::*', root, expected=set(namespaces))

            root = self.etree.XML('<tst:A xmlns:tst="http://xpath.test/ns" '
                                  'xmlns="http://xpath.test/ns"><B1/></tst:A>')
            namespaces = namespaces + [(None, 'http://xpath.test/ns')]
            self.check_selector('/tst:A/namespace::*', root, set(namespaces),
                                namespaces=namespaces[-2:-1])

    def test_parent_shortcut_and_axis(self):
        root = self.etree.XML(
            '<A><B1><C1/></B1><B2/><B3><C1/><C2/></B3><B4><C3><D1/></C3></B4></A>')
        self.check_selector('/A/*/C2/..', root, [root[2]])
        self.check_selector('/A/*/*/..', root, [root[0], root[2], root[3]])
        self.check_selector('//C2/..', root, [root[2]])
        self.check_selector('/A/*/C2/parent::node()', root, [root[2]])
        self.check_selector('/A/*/*/parent::node()', root, [root[0], root[2], root[3]])
        self.check_selector('//C2/parent::node()', root, [root[2]])
        self.check_value('..', MissingContextError)

    def test_ancestor_axes(self):
        root = self.etree.XML(
            '<A><B1><C1/></B1><B2><C1/><D2><E1/><E2/></D2><C2/></B2><B3><C1><D1/></C1></B3></A>')
        self.check_selector('/A/B3/C1/ancestor::*', root, [root, root[2]])
        self.check_selector('/A/B4/C1/ancestor::*', root, [])
        self.check_selector('/A/*/C1/ancestor::*', root, [root, root[0], root[1], root[2]])
        self.check_selector('/A/*/C1/ancestor::B3', root, [root[2]])
        self.check_selector('/A/B3/C1/ancestor-or-self::*', root, [root, root[2], root[2][0]])
        self.check_selector('/A/*/C1/ancestor-or-self::*', root, [
            root, root[0], root[0][0], root[1], root[1][0], root[2], root[2][0]
        ])

    def test_preceding_axis(self):
        root = self.etree.XML('<A><B1><C1/><C2/><C3/></B1><B2><C1/><C2/><C3/><C4/></B2></A>')
        self.check_selector('/A/B1/C2/preceding::*', root, [root[0][0]])
        self.check_selector('/A/B2/C4/preceding::*', root, [
            root[0], root[0][0], root[0][1], root[0][2], root[1][0], root[1][1], root[1][2]
        ])
        root = self.etree.XML("<root><e><a><b/></a><a><b/></a></e><e><a/></e></root>")

        self.check_tree("/root/e/preceding::b", '(/ (/ (/ (root)) (e)) (preceding (b)))')
        self.check_selector('/root/e[2]/preceding::b', root, [root[0][0][0], root[0][1][0]])

    def test_preceding_sibling_axis(self):
        root = self.etree.XML('<A><B1><C1/><C2/><C3/></B1><B2><C1/><C2/><C3/><C4/></B2></A>')
        self.check_selector('/A/B1/C2/preceding-sibling::*', root, [root[0][0]])
        self.check_selector('/A/B2/C4/preceding-sibling::*', root,
                            [root[1][0], root[1][1], root[1][2]])
        self.check_selector('/A/B1/C2/preceding-sibling::C3', root, [])

    def test_default_axis(self):
        """Tests about when child:: default axis is applied."""
        root = self.etree.XML('<root><a id="1">first<b/></a><a id="2">second</a></root>')
        self.check_selector('/root/a/*', root, [root[0][0]])
        self.check_selector('/root/a/b', root, [root[0][0]])
        self.check_selector('/root/a/node()', root, ['first', root[0][0], 'second'])
        self.check_selector('/root/a/text()', root, ['first', 'second'])
        self.check_selector('/root/a/attribute::*', root, ['1', '2'])
        if self.parser.version > '1.0':
            self.check_selector('/root/a/true()', root, [True, True])
            self.check_selector('/root/a/attribute()', root, ['1', '2'])
            self.check_selector('/root/a/element()', root, [root[0][0]])
            self.check_selector('/root/a/name()', root, ['a', 'a'])
            self.check_selector('/root/a/last()', root, [2, 2])
            self.check_selector('/root/a/position()', root, [1, 2])
        else:
            # Functions are not allowed after path step in XPath 1.0
            self.wrong_syntax('/root/a/true()')

    def test_unknown_axis(self):
        self.check_value('unknown::node()', NameError)

    def test_predicate(self):
        root = self.etree.XML('<A><B1><C1/><C2/><C3/></B1><B2><C1/><C2/><C3/><C4/></B2></A>')
        self.check_selector('/A/B1[C2]', root, [root[0]])
        self.check_selector('/A/B1[1]', root, [root[0]])
        self.check_selector('/A/B1[2]', root, [])
        self.check_selector('/A/*[2]', root, [root[1]])
        self.check_selector('/A/*[position()<2]', root, [root[0]])
        self.check_selector('/A/*[last()-1]', root, [root[0]])
        self.check_selector('/A/B2/*[position()>=2]', root, root[1][1:])

        root = self.etree.XML("<bib><book><author>Asimov</author></book></bib>")
        self.check_selector("book/author[. = 'Asimov']", root, [root[0][0]])
        self.check_selector("book/author[. = 'Dickens']", root, [])
        self.check_selector("book/author[text()='Asimov']", root, [root[0][0]])

        root = self.etree.XML('<A><B1>hello</B1><B2/><B3>  </B3></A>')
        self.check_selector("/A/*[' ']", root, root[:])
        self.check_selector("/A/*['']", root, [])

        root = self.etree.XML("<root><a><b/></a><a><b/><c/></a><a><c/></a></root>")

        self.check_tree("child::a[b][c]", '([ ([ (child (a)) (b)) (c))')
        self.check_selector("child::a[b][c]", root, [root[1]])

        root = self.etree.XML("<root><e><a><b/></a><a><b/></a></e><e><a/></e></root>")
        self.check_tree("a[not(b)]", '([ (a) (not (b)))')

        self.check_value("a[not(b)]", [], context=XPathContext(root, item=root[0]))
        self.check_value("a[not(b)]", [root[1][0]], context=XPathContext(root, item=root[1]))

        self.check_tree("preceding::a[not(b)]", '([ (preceding (a)) (not (b)))')

        self.check_value("a[preceding::a[not(b)]]", [], context=XPathContext(root, item=root[0]))
        self.check_value("a[preceding::a[not(b)]]", [], context=XPathContext(root, item=root[1]))

    def test_parenthesized_expression(self):
        self.check_value('(6 + 9)', 15)

    def test_union(self):
        root = self.etree.XML(
            '<A min="1" max="10"><B1><C1/><C2/><C3/></B1><B2><C1/><C2/><C3/><C4/></B2><B3/></A>')
        self.check_selector('/A/B2 | /A/B1', root, root[:2])
        self.check_selector('/A/B2 | /A/*', root, root[:])
        self.check_selector('/A/B2 | /A/* | /A/B1', root, root[:])
        self.check_selector('/A/@min | /A/@max', root, {'1', '10'})

    def test_default_namespace(self):
        root = self.etree.XML('<foo>bar</foo>')
        self.check_selector('/foo', root, [root])
        if self.parser.version == '1.0':
            # XPath 1.0 ignores the default namespace
            self.check_selector('/foo', root, [root], namespaces={'': 'ns'})  # foo --> foo
        else:
            self.check_selector('/foo', root, [], namespaces={'': 'ns'})  # foo --> {ns}foo
            self.check_selector('/*:foo', root, [root], namespaces={'': 'ns'})  # foo --> {ns}foo

        root = self.etree.XML('<foo xmlns="ns">bar</foo>')
        self.check_selector('/foo', root, [])
        if type(self.parser) is XPath1Parser:
            self.check_selector('/foo', root, [], namespaces={'': 'ns'})
        else:
            self.check_selector('/foo', root, [root], namespaces={'': 'ns'})

        root = self.etree.XML('<A xmlns="http://xpath.test/ns"><B1/></A>')
        if self.parser.version > '1.0' or not hasattr(root, 'nsmap'):
            self.check_selector("name(tst:B1)", root, 'tst:B1',
                                namespaces={'tst': "http://xpath.test/ns"})
        if self.parser.version > '1.0':
            self.check_selector("name(B1)", root, 'B1', namespaces={'': "http://xpath.test/ns"})
        else:
            # XPath 1.0 ignores the default namespace declarations
            self.check_selector("name(B1)", root, '', namespaces={'': "http://xpath.test/ns"})


@unittest.skipIf(lxml_etree is None, "The lxml library is not installed")
class LxmlXPath1ParserTest(XPath1ParserTest):
    etree = lxml_etree

    def check_selector(self, path, root, expected, namespaces=None, **kwargs):
        """Check using the selector API (the *select* function of the package)."""
        if isinstance(expected, type) and issubclass(expected, Exception):
            self.assertRaises(expected, select, root, path, namespaces,
                              self.parser.__class__, **kwargs)
        else:
            results = select(root, path, namespaces, self.parser.__class__, **kwargs)
            variables = kwargs.get('variables', {})
            if namespaces and '' in namespaces:
                namespaces = {k: v for k, v in namespaces.items() if k}

            if isinstance(expected, set):
                self.assertEqual(
                    set(root.xpath(path, namespaces=namespaces, **variables)), expected
                )
                self.assertEqual(set(results), expected)
            elif not callable(expected):
                self.assertEqual(root.xpath(path, namespaces=namespaces, **variables), expected)
                self.assertEqual(results, expected)
            elif isinstance(expected, type):
                self.assertTrue(isinstance(results, expected))
            else:
                self.assertTrue(expected(results))


if __name__ == '__main__':
    unittest.main()
