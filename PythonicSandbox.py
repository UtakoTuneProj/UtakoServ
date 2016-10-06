import xml.etree.ElementTree as ET

page = {}
tree = ET.parse("getthumb/sm29757355.xml")
root = tree.getroot()
for child in root[0]:#xmlの辞書化
    page[child.tag] = child.text

print(root.attrib)

if root.attrib['status'] == 'fail':
    raise
