#!/usr/bin/env python
import pathlib
import markdown
from lxml import etree

rst_indent = "   "
tmp_dir: pathlib.Path = pathlib.Path('temp')
root_dir: pathlib.Path = pathlib.Path('../..')

README: str = (root_dir / "README.md").read_text()

# credit to https://stackoverflow.com/a/30737066
doc: etree._Element = etree.fromstring(f"<div>\n{markdown.markdown(README)}\n</div>")

internal_links = [href for link in doc.xpath('//a') if not ':' in (href:=link.get('href'))]

for href in internal_links:
    source: pathlib.Path = root_dir / href
    target: pathlib.Path = tmp_dir / href
    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    target.symlink_to(pathlib.Path(len(target.resolve().parent.relative_to(pathlib.Path.cwd()).parents)*'../') / source)
    if source.suffix not in ['.md', '.rst', '.ipynb']:
        target.with_suffix('.rst').write_text(   
f"""{target.name}
{len(target.name)*'='}

.. literalinclude:: {href}
{rst_indent}:language: none
""")

(tmp_dir / "README.md").write_text(README)

index_toc_lines_list = [
    ".. toctree::",
    ":maxdepth: 2",
    ":caption: Contents:",
    "",
    f"Introduction <{tmp_dir}/README.md>"
    ] + [f"{tmp_dir / href}" for href in internal_links] + [
    "reference.rst"
    ]

(tmp_dir / "index_toc").write_text(("\n"+rst_indent).join(index_toc_lines_list))
