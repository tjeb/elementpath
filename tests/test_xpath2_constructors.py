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
import unittest
import datetime
import platform
from decimal import Decimal

try:
    import lxml.etree as lxml_etree
except ImportError:
    lxml_etree = None

from elementpath import XPathContext, AttributeNode
from elementpath.datatypes import Timezone, DateTime, GregorianYear10, \
    Duration, YearMonthDuration, DayTimeDuration, Date10, Time, \
    XPathGregorianDay, XPathGregorianMonth, XPathGregorianMonthDay, \
    XPathGregorianYear, XPathGregorianYearMonth, UntypedAtomic

try:
    from tests import xpath_test_class
except ImportError:
    import xpath_test_class


class XPath2ConstructorsTest(xpath_test_class.XPathTestCase):

    def test_string_constructor(self):
        self.check_value("xs:string(5.0)", '5.0')
        self.check_value('xs:string(" hello  ")', ' hello  ')
        self.check_value('xs:string("\thello \n")', '\thello \n')
        self.check_value('xs:string(())', [])

    def test_normalized_string_constructor(self):
        self.check_value('xs:normalizedString("hello")', "hello")
        self.check_value('xs:normalizedString(" hello  ")', " hello  ")
        self.check_value('xs:normalizedString("\thello \n")', " hello  ")
        self.check_value('xs:normalizedString(())', [])

        root = self.etree.XML('<root a="\t alpha \n\tbeta "/>')
        context = XPathContext(root)
        self.check_value('xs:normalizedString(@a)', '  alpha   beta ', context=context)

    def test_token_constructor(self):
        self.check_value('xs:token(" hello  world ")', "hello world")
        self.check_value('xs:token("hello\t world\n")', "hello world")
        self.check_value('xs:token(xs:untypedAtomic("hello\t world\n"))', "hello world")
        self.check_value('xs:token(())', [])

        root = self.etree.XML('<root a=" hello  world "/>')
        context = XPathContext(root)
        self.check_value('xs:token(@a)', 'hello world', context=context)

    def test_language_constructor(self):
        self.check_value('xs:language(" en ")', "en")
        self.check_value('xs:language(xs:untypedAtomic(" en "))', "en")
        self.check_value('xs:language(" en-GB ")', "en-GB")
        self.check_value('xs:language("it-IT")', "it-IT")
        self.check_value('xs:language("i-klingon")', 'i-klingon')  # IANA-registered language
        self.check_value('xs:language("x-another-language-code")', 'x-another-language-code')
        self.wrong_value('xs:language("MoreThan8")')
        self.check_value('xs:language(())', [])

        root = self.etree.XML('<root a=" en-US "/>')
        context = XPathContext(root)
        self.check_value('xs:language(@a)', 'en-US', context=context)

    def test_nmtoken_constructor(self):
        self.check_value('xs:NMTOKEN(" :menù.09-_ ")', ":menù.09-_")
        self.check_value('xs:NMTOKEN(xs:untypedAtomic(" :menù.09-_ "))', ":menù.09-_")
        self.wrong_value('xs:NMTOKEN("alpha+")')
        self.wrong_value('xs:NMTOKEN("hello world")')
        self.check_value('xs:NMTOKEN(())', [])

        root = self.etree.XML('<root a=" tns:example "/>')
        context = XPathContext(root)
        self.check_value('xs:NMTOKEN(@a)', 'tns:example', context=context)

    def test_name_constructor(self):
        self.check_value('xs:Name(" :base ")', ":base")
        self.check_value('xs:Name(xs:untypedAtomic(" :base "))', ":base")
        self.check_value('xs:Name(" ::level_alpha ")', "::level_alpha")
        self.check_value('xs:Name("level-alpha")', "level-alpha")
        self.check_value('xs:Name("level.alpha\t\n")', "level.alpha")
        self.check_value('xs:Name("__init__ ")', "__init__")
        self.check_value('xs:Name("\u0110")', "\u0110")
        self.wrong_value('xs:Name("2_values")')
        self.wrong_value('xs:Name(" .values ")')
        self.wrong_value('xs:Name(" -values ")')
        self.check_value('xs:Name(())', [])

        root = self.etree.XML('<root a=" :foo: "/>')
        context = XPathContext(root)
        self.check_value('xs:Name(@a)', ':foo:', context=context)

    def test_ncname_constructor(self):
        self.check_value('xs:NCName(" base ")', "base")
        self.check_value('xs:NCName(xs:untypedAtomic(" base "))', "base")
        self.check_value('xs:NCName(" _level_alpha ")', "_level_alpha")
        self.check_value('xs:NCName("level-alpha")', "level-alpha")
        self.check_value('xs:NCName("level.alpha\t\n")', "level.alpha")
        self.check_value('xs:NCName("__init__ ")', "__init__")
        self.check_value('xs:NCName("\u0110")', "\u0110")
        self.wrong_value('xs:NCName("2_values")')
        self.wrong_value('xs:NCName(" .values ")')
        self.wrong_value('xs:NCName(" -values ")')
        self.check_value('xs:NCName(())', [])

        self.wrong_value('xs:NCName("tns:example")')

        root = self.etree.XML('<root a=" foo "/>')
        context = XPathContext(root)
        self.check_value('xs:NCName(@a)', 'foo', context=context)

    def test_id_constructor(self):
        self.check_value('xs:ID("xyz")', 'xyz')
        self.check_value('xs:ID(xs:untypedAtomic("xyz"))', 'xyz')

    def test_idref_constructor(self):
        self.check_value('xs:IDREF("xyz")', 'xyz')
        self.check_value('xs:IDREF(xs:untypedAtomic("xyz"))', 'xyz')

    def test_entity_constructor(self):
        self.check_value('xs:ENTITY("xyz")', 'xyz')
        self.check_value('xs:ENTITY(xs:untypedAtomic("xyz"))', 'xyz')

    def test_qname_constructor(self):
        self.check_value('xs:QName(())', [])
        self.check_value('xs:QName("xs:element")', 'xs:element')
        self.check_value('xs:QName(xs:untypedAtomic("xs:element"))', 'xs:element')
        self.assertRaises(KeyError, self.parser.parse, 'xs:QName("xsd:element")')
        self.wrong_type('xs:QName(5)', 'FORG0006', "the argument has an invalid type")
        self.wrong_value('xs:QName("1")', 'FOCA0002', "the argument must be an xs:QName")

    def test_any_uri_constructor(self):
        self.check_value('xs:anyURI("")', '')
        self.check_value('xs:anyURI("https://example.com")', 'https://example.com')
        self.check_value('xs:anyURI("mailto:info@example.com")', 'mailto:info@example.com')
        self.check_value('xs:anyURI("urn:example:com")', 'urn:example:com')
        self.check_value('xs:anyURI(xs:untypedAtomic("urn:example:com"))', 'urn:example:com')
        self.check_value('xs:anyURI("../principi/libertà.html")', '../principi/libertà.html')
        self.check_value('xs:anyURI("../principi/libert%E0.html")', '../principi/libert%E0.html')
        self.check_value('xs:anyURI("../path/page.html#frag")', '../path/page.html#frag')
        self.wrong_value('xs:anyURI("../path/page.html#frag1#frag2")')
        self.wrong_value('xs:anyURI("https://example.com/index%.html")')
        self.wrong_value('xs:anyURI("https://example.com/index.%html")')
        self.wrong_value('xs:anyURI("https://example.com/index.html%  frag")')
        self.check_value('xs:anyURI(())', [])

        if platform.python_version_tuple() >= ('3', '6') and \
                platform.python_implementation() != 'PyPy':
            self.wrong_value('xs:anyURI("https://example.com:65536")',
                             'FOCA0002', 'Port out of range 0-65535')

        root = self.etree.XML('<root a=" https://example.com "/>')
        context = XPathContext(root)
        self.check_value('xs:anyURI(@a)', 'https://example.com', context=context)

    def test_boolean_constructor(self):
        self.check_value('xs:boolean(())', [])
        self.check_value('xs:boolean(1)', True)
        self.check_value('xs:boolean(0)', False)
        self.check_value('xs:boolean(xs:boolean(0))', False)
        self.check_value('xs:boolean(xs:untypedAtomic(0))', False)
        self.wrong_type('xs:boolean(xs:hexBinary("FF"))', 'FORG0006', "<class 'bytes'>")
        self.wrong_value('xs:boolean("2")', 'FOCA0002', "not a boolean value")

    def test_integer_constructors(self):
        self.wrong_value('xs:integer("hello")', 'FORG0001')
        self.check_value('xs:integer("19")', 19)
        self.check_value('xs:integer(xs:untypedAtomic("19"))', 19)
        self.check_value("xs:integer('-5')", -5)

        root = self.etree.XML('<root a="19"/>')
        context = XPathContext(root)
        self.check_value('xs:integer(@a)', 19, context=context)

        root = self.etree.XML('<root/>')
        context = XPathContext(root, item=float('nan'))
        self.check_value('xs:integer(.)', ValueError, context=context)

        self.wrong_value('xs:nonNegativeInteger("-1")')
        self.wrong_value('xs:nonNegativeInteger(-1)')
        self.check_value('xs:nonNegativeInteger(0)', 0)
        self.check_value('xs:nonNegativeInteger(1000)', 1000)
        self.wrong_value('xs:positiveInteger(0)')
        self.check_value('xs:positiveInteger("1")', 1)
        self.wrong_value('xs:negativeInteger(0)')
        self.check_value('xs:negativeInteger(-1)', -1)
        self.wrong_value('xs:nonPositiveInteger(1)')
        self.check_value('xs:nonPositiveInteger(0)', 0)
        self.check_value('xs:nonPositiveInteger("-1")', -1)

    def test_limited_integer_constructors(self):
        self.wrong_value('xs:long("true")')
        self.wrong_value('xs:long("340282366920938463463374607431768211456")')
        self.check_value('xs:long("-20")', -20)
        self.wrong_value('xs:int("-20 91")')
        self.wrong_value('xs:int("9223372036854775808")')
        self.check_value('xs:int("-9223372036854775808")', -2**63)
        self.check_value('xs:int("4611686018427387904")', 2**62)
        self.wrong_value('xs:short("40000")')
        self.check_value('xs:short("9999")', 9999)
        self.check_value('xs:short(-9999)', -9999)
        self.wrong_value('xs:byte(-129)')
        self.wrong_value('xs:byte(128)')
        self.check_value('xs:byte("-128")', -128)
        self.check_value('xs:byte(127)', 127)
        self.check_value('xs:byte(-90)', -90)

        self.wrong_value('xs:unsignedLong("-10")')
        self.check_value('xs:unsignedLong("3")', 3)
        self.wrong_value('xs:unsignedInt("-9223372036854775808")')
        self.check_value('xs:unsignedInt("9223372036854775808")', 2**63)
        self.wrong_value('xs:unsignedShort("-1")')
        self.check_value('xs:unsignedShort("0")', 0)
        self.wrong_value('xs:unsignedByte(-128)')
        self.check_value('xs:unsignedByte("128")', 128)

    def test_decimal_constructors(self):
        self.wrong_value('xs:decimal("hello")')
        self.check_value('xs:decimal("19")', 19)
        self.check_value('xs:decimal("19")', Decimal)
        self.check_value('xs:decimal(xs:untypedAtomic("19"))', 19)

        root = self.etree.XML('<root a="10.3"/>')
        context = XPathContext(root)
        self.check_value('xs:decimal(@a)', Decimal('10.3'), context=context)

    def test_double_constructor(self):
        self.wrong_value('xs:double("world")')
        self.check_value('xs:double("39.09")', 39.09)
        self.check_value('xs:double(xs:untypedAtomic("39.09"))', 39.09)
        self.check_value('xs:double(-5)', -5.0)
        self.check_value('xs:double(-5)', float)

        root = self.etree.XML('<root a="10.3"/>')
        context = XPathContext(root, item=AttributeNode('a', 10.3))
        self.check_value('xs:double(.)', float, context=context)
        self.check_value('xs:double(.)', 10.3, context=context)

    def test_float_constructor(self):
        self.wrong_value('xs:float("..")')
        self.check_value('xs:float(25.05)', 25.05)
        self.check_value('xs:float(xs:untypedAtomic(25.05))', 25.05)
        self.check_value('xs:float(-0.00001)', -0.00001)
        self.check_value('xs:float(0.00001)', float)

        root = self.etree.XML('<root a="10.3"/>')
        context = XPathContext(root, item=AttributeNode('a', 10.3))
        self.check_value('xs:float(.)', float, context=context)
        self.check_value('xs:float(.)', 10.3, context=context)

    def test_datetime_constructor(self):
        tz0 = None
        tz1 = Timezone(datetime.timedelta(hours=5, minutes=24))
        self.check_value('xs:dateTime(())', [])
        self.check_value('xs:dateTime("1969-07-20T20:18:00")',
                         DateTime(1969, 7, 20, 20, 18, tzinfo=tz0))
        self.check_value('xs:dateTime(xs:untypedAtomic("1969-07-20T20:18:00"))',
                         DateTime(1969, 7, 20, 20, 18, tzinfo=tz0))
        self.check_value('xs:dateTime("2000-05-10T21:30:00+05:24")',
                         datetime.datetime(2000, 5, 10, hour=21, minute=30, tzinfo=tz1))
        self.check_value('xs:dateTime("1999-12-31T24:00:00")',
                         datetime.datetime(2000, 1, 1, 0, 0, tzinfo=tz0))

        self.wrong_value('xs:dateTime("2000-05-10t21:30:00+05:24")')
        self.wrong_value('xs:dateTime("2000-5-10T21:30:00+05:24")')
        self.wrong_value('xs:dateTime("2000-05-10T21:3:00+05:24")')
        self.wrong_value('xs:dateTime("2000-05-10T21:13:0+05:24")')
        self.wrong_value('xs:dateTime("2000-05-10T21:13:0")')
        self.wrong_type('xs:dateTime(50)', 'FORG0006', '1st argument has an invalid type')

        root = self.etree.XML('<root a="1969-07-20T20:18:00"/>')
        context = XPathContext(root)
        self.check_value('xs:dateTime(@a)', DateTime(1969, 7, 20, 20, 18), context=context)

        context.item = AttributeNode('a', DateTime(1969, 7, 20, 20, 18))
        self.check_value('xs:dateTime(.)', DateTime(1969, 7, 20, 20, 18), context=context)

        context.item = AttributeNode('a', True)
        self.check_value('xs:dateTime(.)', TypeError, context=context)

    def test_time_constructor(self):
        tz0 = None
        tz1 = Timezone(datetime.timedelta(hours=5, minutes=24))
        self.check_value('xs:time("21:30:00")',
                         datetime.datetime(2000, 1, 1, 21, 30, tzinfo=tz0))
        self.check_value('xs:time(xs:untypedAtomic("21:30:00"))',
                         datetime.datetime(2000, 1, 1, 21, 30, tzinfo=tz0))
        self.check_value('xs:time("11:15:48+05:24")',
                         datetime.datetime(2000, 1, 1, 11, 15, 48, tzinfo=tz1))

        root = self.etree.XML('<root a="13:15:39"/>')
        context = XPathContext(root)
        self.check_value('xs:time(@a)', Time(13, 15, 39), context=context)

        context.item = Time(20, 10, 00)
        self.check_value('xs:time(.)', Time(20, 10, 00), context=context)

    def test_date_constructor(self):
        tz0 = None
        tz2 = Timezone(datetime.timedelta(hours=-14, minutes=0))

        self.check_value('xs:date("2017-01-19")',
                         datetime.datetime(2017, 1, 19, tzinfo=tz0))
        self.check_value('xs:date(xs:untypedAtomic("2017-01-19"))',
                         datetime.datetime(2017, 1, 19, tzinfo=tz0))
        self.check_value('xs:date("2011-11-11-14:00")',
                         datetime.datetime(2011, 11, 11, tzinfo=tz2))
        self.wrong_value('xs:date("2011-11-11-14:01")')
        self.wrong_value('xs:date("11-11-11")')
        self.check_value('xs:date(())', [])

        root = self.etree.XML('<root a="2017-01-19"/>')
        context = XPathContext(root)
        self.check_value('xs:date(@a)', Date10(2017, 1, 19), context=context)

        context.item = AttributeNode('a', Date10(2017, 1, 19))
        self.check_value('xs:date(.)', Date10(2017, 1, 19), context=context)

        context.item = AttributeNode('a', True)
        self.check_value('xs:date(.)', TypeError, context=context)

    def test_gregorian_day_constructor(self):
        tz0 = None
        tz1 = Timezone(datetime.timedelta(hours=5, minutes=24))

        self.check_value('xs:gDay("---30")',
                         datetime.datetime(2000, 1, 30, tzinfo=tz0))
        self.check_value('xs:gDay(xs:untypedAtomic("---30"))',
                         datetime.datetime(2000, 1, 30, tzinfo=tz0))
        self.check_value('xs:gDay("---21+05:24")',
                         datetime.datetime(2000, 1, 21, tzinfo=tz1))
        self.wrong_value('xs:gDay("---32")')
        self.wrong_value('xs:gDay("--19")')

        root = self.etree.XML('<root a="---08"/>')
        context = XPathContext(root)
        self.check_value('xs:gDay(@a)', XPathGregorianDay(8), context=context)

        context.item = XPathGregorianDay(10)
        self.check_value('xs:gDay(.)', XPathGregorianDay(10), context=context)

    def test_gregorian_month_constructor(self):
        self.check_value('xs:gMonth("--09")', datetime.datetime(2000, 9, 1))
        self.check_value('xs:gMonth(xs:untypedAtomic("--09"))', datetime.datetime(2000, 9, 1))
        self.check_value('xs:gMonth("--12")', datetime.datetime(2000, 12, 1))
        self.wrong_value('xs:gMonth("--9")')
        self.wrong_value('xs:gMonth("-09")')
        self.wrong_value('xs:gMonth("--13")')

        root = self.etree.XML('<root a="--11"/>')
        context = XPathContext(root)
        self.check_value('xs:gMonth(@a)', XPathGregorianMonth(11), context=context)

        context.item = XPathGregorianMonth(1)
        self.check_value('xs:gMonth(.)', XPathGregorianMonth(1), context=context)

    def test_gregorian_month_day_constructor(self):
        tz0 = None
        tz2 = Timezone(datetime.timedelta(hours=-14, minutes=0))

        self.check_value('xs:gMonthDay("--07-02")',
                         datetime.datetime(2000, 7, 2, tzinfo=tz0))
        self.check_value('xs:gMonthDay(xs:untypedAtomic("--07-02"))',
                         datetime.datetime(2000, 7, 2, tzinfo=tz0))
        self.check_value('xs:gMonthDay("--07-02-14:00")',
                         datetime.datetime(2000, 7, 2, tzinfo=tz2))
        self.wrong_value('xs:gMonthDay("--7-02")')
        self.wrong_value('xs:gMonthDay("-07-02")')
        self.wrong_value('xs:gMonthDay("--07-32")')

        root = self.etree.XML('<root a="--05-20"/>')
        context = XPathContext(root)
        self.check_value('xs:gMonthDay(@a)', XPathGregorianMonthDay(5, 20), context=context)

        context.item = XPathGregorianMonthDay(1, 15)
        self.check_value('xs:gMonthDay(.)', XPathGregorianMonthDay(1, 15), context=context)

    def test_gregorian_year_constructor(self):
        self.check_value('xs:gYear("2004")', datetime.datetime(2004, 1, 1))
        self.check_value('xs:gYear(xs:untypedAtomic("2004"))', datetime.datetime(2004, 1, 1))
        self.check_value('xs:gYear("-2004")', GregorianYear10(-2004))
        self.check_value('xs:gYear("-12540")', GregorianYear10(-12540))
        self.check_value('xs:gYear("12540")', GregorianYear10(12540))
        self.wrong_value('xs:gYear("84")')
        self.wrong_value('xs:gYear("821")')
        self.wrong_value('xs:gYear("84")')

        root = self.etree.XML('<root a="1999"/>')
        context = XPathContext(root)
        self.check_value('xs:gYear(@a)', XPathGregorianYear(1999), context=context)

        context.item = XPathGregorianYear(1492)
        self.check_value('xs:gYear(.)', XPathGregorianYear(1492), context=context)

    def test_gregorian_year_month_constructor(self):
        self.check_value('xs:gYearMonth("2004-02")',
                         datetime.datetime(2004, 2, 1))
        self.check_value('xs:gYearMonth(xs:untypedAtomic("2004-02"))',
                         datetime.datetime(2004, 2, 1))
        self.wrong_value('xs:gYearMonth("2004-2")')
        self.wrong_value('xs:gYearMonth("204-02")')

        root = self.etree.XML('<root a="1900-01"/>')
        context = XPathContext(root)
        self.check_value('xs:gYearMonth(@a)', XPathGregorianYearMonth(1900, 1), context=context)

        context.item = XPathGregorianYearMonth(1300, 10)
        self.check_value('xs:gYearMonth(.)', XPathGregorianYearMonth(1300, 10), context=context)

    def test_duration_constructor(self):
        self.check_value('xs:duration("P3Y5M1D")', (41, 86400))
        self.check_value('xs:duration(xs:untypedAtomic("P3Y5M1D"))', (41, 86400))
        self.check_value('xs:duration("P3Y5M1DT1H")', (41, 90000))
        self.check_value('xs:duration("P3Y5M1DT1H3M2.01S")', (41, Decimal('90182.01')))
        self.wrong_value('xs:duration("P3Y5M1X")')
        self.assertRaises(TypeError, self.parser.parse, 'xs:duration(1)')

        root = self.etree.XML('<root a="P1Y5M"/>')
        context = XPathContext(root)
        self.check_value('xs:duration(@a)', Duration(months=17), context=context)

        context.item = Duration(months=12, seconds=86400)
        self.check_value('xs:duration(.)', Duration(12, 86400), context=context)

    def test_year_month_duration_constructor(self):
        self.check_value('xs:yearMonthDuration("P3Y5M")', (41, 0))
        self.check_value('xs:yearMonthDuration(xs:untypedAtomic("P3Y5M"))', (41, 0))
        self.check_value('xs:yearMonthDuration("-P15M")', (-15, 0))
        self.check_value('xs:yearMonthDuration("-P20Y18M")',
                         YearMonthDuration.fromstring("-P21Y6M"))
        self.wrong_value('xs:yearMonthDuration("-P15M1D")')
        self.wrong_value('xs:yearMonthDuration("P15MT1H")')
        self.wrong_value('xs:yearMonthDuration("P1MT10H")')

        root = self.etree.XML('<root a="P1Y5M"/>')
        context = XPathContext(root)
        self.check_value('xs:yearMonthDuration(@a)', Duration(months=17), context=context)

        context.item = YearMonthDuration(months=12)
        self.check_value('xs:yearMonthDuration(.)', YearMonthDuration(12), context=context)

    def test_day_time_duration_constructor(self):
        self.check_value('xs:dayTimeDuration("-P2DT15H")', DayTimeDuration(seconds=-226800))
        self.check_value('xs:dayTimeDuration("PT240H")', DayTimeDuration.fromstring("P10D"))
        self.check_value('xs:dayTimeDuration("P365D")', DayTimeDuration.fromstring("P365D"))
        self.check_value('xs:dayTimeDuration(xs:untypedAtomic("PT240H"))',
                         DayTimeDuration.fromstring("P10D"))
        self.check_value('xs:dayTimeDuration("-P2DT15H0M0S")',
                         DayTimeDuration.fromstring('-P2DT15H'))
        self.check_value('xs:dayTimeDuration("P3DT10H")', DayTimeDuration.fromstring("P3DT10H"))
        self.check_value('xs:dayTimeDuration("PT1S")', (0, 1))
        self.check_value('xs:dayTimeDuration("PT0S")', (0, 0))

        root = self.etree.XML('<root a="P5DT18H"/>')
        context = XPathContext(root)
        self.check_value('xs:dayTimeDuration(@a)', DayTimeDuration(496800), context=context)

        context.item = DayTimeDuration(86400)
        self.check_value('xs:dayTimeDuration(.)', DayTimeDuration(86400), context=context)

    def test_hex_binary_constructor(self):
        self.check_value('xs:hexBinary(())', [])
        self.check_value('xs:hexBinary("84")', b'3834')
        self.check_value('xs:hexBinary(xs:hexBinary("84"))', b'3834')
        self.wrong_type('xs:hexBinary(12)')

        root = self.etree.XML('<root a="84"/>')
        context = XPathContext(root)
        self.check_value('xs:hexBinary(@a)', b'3834', context=context)

        context.item = UntypedAtomic('84')
        self.check_value('xs:hexBinary(.)', b'3834', context=context)

        context.item = '84'
        self.check_value('xs:hexBinary(.)', b'3834', context=context)

        context.item = b'84'
        self.check_value('xs:hexBinary(.)', b'84', context=context)

        context.item = b'XY'
        self.check_value('xs:hexBinary(.)', b'5859', context=context)

        context.item = b'ODQ='
        if platform.python_implementation() != 'PyPy':
            # Skip for PyPy because PyPy 7.1.1-beta0 has a bug on codecs.decode()
            self.check_value('xs:hexBinary(.)', b'3834', context=context)

    def test_base64_binary_constructor(self):
        self.check_value('xs:base64Binary(())', [])
        self.check_value('xs:base64Binary("84")', b'ODQ=\n')
        self.check_value('xs:base64Binary(xs:base64Binary("84"))', b'ODQ=\n')
        self.check_value('xs:base64Binary("abcefghi")', b'YWJjZWZnaGk=\n')
        self.wrong_type('xs:base64Binary(1e2)')
        self.wrong_type('xs:base64Binary(1.1)')

        root = self.etree.XML('<root a="abcefghi"/>')
        context = XPathContext(root)
        self.check_value('xs:base64Binary(@a)', b'YWJjZWZnaGk=\n', context=context)

        context.item = UntypedAtomic('abcefghi')
        self.check_value('xs:base64Binary(.)', b'YWJjZWZnaGk=\n', context=context)

        context.item = b'FF'
        if platform.python_implementation() != 'PyPy':
            # Skip for PyPy because PyPy 7.1.1-beta0 has a bug on codecs.decode()
            self.check_value('xs:base64Binary(.)', b'/w==\n', context=context)

        context.item = b'abcefghi'  # Don't change, it can be an encoded value.
        self.check_value('xs:base64Binary(.)', b'abcefghi', context=context)

        context.item = b'abcefghij'
        self.check_value('xs:base64Binary(.)', b'YWJjZWZnaGlq\n', context=context)


@unittest.skipIf(lxml_etree is None, "The lxml library is not installed")
class LxmlXPath2ConstructorsTest(XPath2ConstructorsTest):
    etree = lxml_etree


if __name__ == '__main__':
    unittest.main()
