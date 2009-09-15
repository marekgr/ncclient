# Copyright 2009 Shikhar Bhushan
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""The :mod:`xml` module provides methods for creating XML documents, parsing
XML, and converting between different XML representations. It uses
:mod:`~xml.etree.ElementTree` internally.
"""

from cStringIO import StringIO
from xml.etree import cElementTree as ET

from ncclient import NCClientError

class XMLError(NCClientError):
    pass

### Namespace-related

#: Base NETCONF namespace
BASE_NS_1_0 = 'urn:ietf:params:xml:ns:netconf:base:1.0'
#: namespace for Tail-f data model
TAILF_AAA_1_1 = 'http://tail-f.com/ns/aaa/1.1'
#: namespace for Tail-f data model
TAILF_EXECD_1_1 = 'http://tail-f.com/ns/execd/1.1'
#: namespace for Cisco data model
CISCO_CPI_1_0 = 'http://www.cisco.com/cpi_10/schema'
#: namespace for Flowmon data model
FLOWMON_1_0 = 'http://www.liberouter.org/ns/netopeer/flowmon/1.0'

try:
    register_namespace = ET.register_namespace
except AttributeError:
    def register_namespace(prefix, uri):
        from xml.etree import ElementTree
        # cElementTree uses ElementTree's _namespace_map, so that's ok
        ElementTree._namespace_map[uri] = prefix

prefix_map = {
    BASE_NS_1_0: 'nc',
    TAILF_AAA_1_1: 'aaa',
    TAILF_EXECD_1_1: 'execd',
    CISCO_CPI_1_0: 'cpi',
    FLOWMON_1_0: 'fm',
}

for (ns, pre) in prefix_map.items():
    register_namespace(pre, ns)

qualify = lambda tag, ns=BASE_NS_1_0: tag if ns is None else '{%s}%s' % (ns, tag)

#unqualify = lambda tag: tag[tag.rfind('}')+1:]

def to_xml(ele, encoding="UTF-8"):
    """Element -> XML
    
    :type spec: :class:`~xml.etree.ElementTree.Element`
    :arg encoding: character encoding
    :rtype: :obj:`string`
    """
    xml = ET.tostring(ele, encoding)
    return xml if xml.startswith('<?xml') else '<?xml version="1.0" encoding="%s"?>%s' % (encoding, xml)

def to_ele(x):
    """XML -> Element
    
    :type xml: :obj:`string`
    :rtype: :class:`~xml.etree.ElementTree.Element`
    """
    return x if iselement(x) else ET.fromstring(x)

iselement = ET.iselement

def parse_root(raw):
    """Efficiently parses the root element of an XML document.

    :arg raw: XML document
    :type raw: string
    :returns: a tuple of `(tag, attributes)`, where `tag` is the (qualified) name of the element and `attributes` is a dictionary of its attributes.
    :rtype: `tuple`
    """
    fp = StringIO(raw)
    for event, element in ET.iterparse(fp, events=('start',)):
        return (element.tag, element.attrib)

def validated_element(x, tags=None, attrs=None):
    """Checks if the root element meets the supplied criteria. Returns a
    :class:`~xml.etree.ElementTree.Element` instance if so, otherwise raises
    :exc:`ContentError`.

    :arg tags: tag name or a sequence of allowable tag names
    :arg attrs: sequence of required attribute names, each item may be a list of allowable alternatives
    :arg text: textual content to match
    :type rep: :class:`~xml.etree.ElementTree.Element`
    """
    ele = to_ele(x)
    if tags:
        if isinstance(tags, basestring):
            tags = [tags]
        if ele.tag not in tags:
            raise XMLError("Element [%s] does not meet requirement" % ele.tag)
    if attrs:
        for req in attrs:
            if isinstance(req, basestring): req = [req]
            for alt in req:
                if alt in ele.attrib:
                    break
            else:
                raise XMLError("Element [%s] does not have required attributes" % ele.tag)
    return ele

def new_ele(tag, attrs={}, **extra):
    return ET.Element(tag, attrs, **extra)

def sub_ele(parent, tag, attrs={}, **extra):
    return ET.SubElement(parent, tag, attrs, **extra)
