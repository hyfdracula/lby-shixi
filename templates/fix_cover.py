"""python-docx 后处理 docx: 标题黑体加粗居中 + 校徽图居中 + 信息居中 + 项目简介前分页。"""
import sys
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def _has_drawing(run) -> bool:
    return bool(run._element.findall(".//" + qn("w:drawing")))


def fix_cover(path: str) -> None:
    doc = Document(path)
    for p in doc.paragraphs:
        t = p.text
        # 校徽图片段居中
        if any(_has_drawing(r) for r in p.runs):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            continue
        # 标题黑体加粗居中大字
        if "基于遥感植被参数" in t and ("湖南" in t or "研究区" in t):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(18)
                r.font.name = "黑体"
                rPr = r._element.get_or_add_rPr()
                rFonts = rPr.find(qn("w:rFonts"))
                if rFonts is None:
                    rFonts = r._element.makeelement(qn("w:rFonts"), {})
                    rPr.append(rFonts)
                for attr in ("w:eastAsia", "w:ascii", "w:hAnsi"):
                    rFonts.set(qn(attr), "黑体")
            continue
        # 信息行居中
        if any(k in t for k in ["学　", "班　", "姓　", "指导教师", "林学院", "地信23", "梁博毅", "2026 年"]):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            continue
        # "一、项目简介" 前分页(封面后正文起在新页)
        if "项目简介" in t:
            p.paragraph_format.page_break_before = True
    doc.save(path)
    print("封面精调完成: 标题黑体加粗居中 + 校徽居中 + 信息居中 + 项目简介前分页")


if __name__ == "__main__":
    fix_cover(sys.argv[1] if len(sys.argv) > 1 else "C:/Users/19161/Desktop/report_hunan_v4.docx")
