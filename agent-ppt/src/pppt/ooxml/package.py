import zipfile
from pathlib import Path
from typing import List, Tuple

from ..constants import CONTENT_TYPE_PNG, CONTENT_TYPE_JPEG, REL_NS
from ..utils import write_text


def write_root_rels(work_dir: Path):
    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="{REL_NS}">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
'''
    write_text(work_dir / "_rels/.rels", xml)


def write_content_types(work_dir: Path, slide_count: int, chart_count: int = 0):
    overrides = [
        ('/ppt/presentation.xml', 'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'),
        ('/ppt/theme/theme1.xml', 'application/vnd.openxmlformats-officedocument.theme+xml'),
        ('/ppt/slideMasters/slideMaster1.xml', 'application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml'),
        ('/ppt/slideLayouts/slideLayout1.xml', 'application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'),
        ('/docProps/core.xml', 'application/vnd.openxmlformats-package.core-properties+xml'),
        ('/docProps/app.xml', 'application/vnd.openxmlformats-officedocument.extended-properties+xml'),
    ]
    for i in range(1, slide_count + 1):
        overrides.append((
            f'/ppt/slides/slide{i}.xml',
            'application/vnd.openxmlformats-officedocument.presentationml.slide+xml'
        ))
    for i in range(1, chart_count + 1):
        overrides.append((
            f'/ppt/charts/chart{i}.xml',
            'application/vnd.openxmlformats-officedocument.drawingml.chart+xml'
        ))

    default_entries = [
        ('rels', 'application/vnd.openxmlformats-package.relationships+xml'),
        ('xml', 'application/xml'),
        ('png', CONTENT_TYPE_PNG),
        ('jpg', CONTENT_TYPE_JPEG),
        ('jpeg', CONTENT_TYPE_JPEG),
    ]

    defaults_xml = "\n".join(
        f'  <Default Extension="{ext}" ContentType="{ctype}"/>'
        for ext, ctype in default_entries
    )
    overrides_xml = "\n".join(
        f'  <Override PartName="{part}" ContentType="{ctype}"/>'
        for part, ctype in overrides
    )

    xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
{defaults_xml}
{overrides_xml}
</Types>
'''
    write_text(work_dir / "[Content_Types].xml", xml)


def zip_to_pptx(work_dir: Path, output_path: Path):
    if output_path.exists():
        output_path.unlink()

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in work_dir.rglob("*"):
            if p.is_file():
                arcname = str(p.relative_to(work_dir)).replace("\\", "/")
                zf.write(p, arcname=arcname)
