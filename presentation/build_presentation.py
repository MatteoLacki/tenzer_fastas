"""Build an editable PowerPoint and matching vector PDF for group discussion."""
from pathlib import Path
import json
import re
from xml.sax.saxutils import escape
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

OUT = Path(__file__).resolve().parent
W, H = 960, 540
NAVY='142B3B'; TEAL='007F7B'; MINT='E3F2ED'; CORAL='D7583D'; PALE='FFF0E9'
BG='F7F8F5'; WHITE='FFFFFF'; INK='203443'; MUTED='5C6D76'; LINE='DCE3DF'
for n,p in [('Lato','/usr/share/fonts/truetype/lato/Lato-Regular.ttf'),('Lato-Bold','/usr/share/fonts/truetype/lato/Lato-Bold.ttf'),('Mono','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(n,p))
prs=Presentation(); prs.slide_width=Inches(W/72); prs.slide_height=Inches(H/72)
prs.core_properties.title='Identical sequences, different labels'
prs.core_properties.subject='Contaminant FASTA duplication and project-specific filtering policy'
prs.core_properties.author='Proteomics group discussion'
pdf=canvas.Canvas(str(OUT/'contaminant_duplicates.pdf'),pagesize=(W,H))
pdf.setTitle(prs.core_properties.title)
slides=[]; errors=[]

def rgb(c): return RGBColor.from_string(c)
def color(c): return tuple(int(c[i:i+2],16)/255 for i in (0,2,4))
def rect(x,y,w,h,fill,round=False,line=None):
    sh=slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if round else MSO_SHAPE.RECTANGLE,Pt(x),Pt(y),Pt(w),Pt(h))
    sh.fill.solid();sh.fill.fore_color.rgb=rgb(fill)
    if line:sh.line.color.rgb=rgb(line)
    else:sh.line.fill.background()
    if round:
        try:sh.adjustments[0]=0.08
        except Exception:pass
    pdf.setFillColorRGB(*color(fill));pdf.setStrokeColorRGB(*color(line or fill))
    if round:pdf.roundRect(x,H-y-h,w,h,9,stroke=bool(line),fill=1)
    else:pdf.rect(x,H-y-h,w,h,stroke=bool(line),fill=1)
    return sh

def text(s,x,y,w,h,size=20,c=INK,bold=False,mono=False,leading=None,link=None):
    font='Mono' if mono else ('Lato-Bold' if bold else 'Lato')
    leading=leading or size*1.22
    lines=[]
    for para in s.split('\n'):
        if not para:lines.append('');continue
        current=''
        for word in para.split(' '):
            candidate=(current+' '+word).strip()
            if pdfmetrics.stringWidth(candidate,font,size)>w-2 and current:
                lines.append(current);current=word
            else:current=candidate
        lines.append(current)
    if len(lines)*leading > h+2:errors.append((len(slides),s[:55],len(lines)*leading,h))
    box=slide.shapes.add_textbox(Pt(x),Pt(y),Pt(w),Pt(h))
    tf=box.text_frame;tf.clear();tf.word_wrap=False
    tf.margin_left=tf.margin_right=tf.margin_top=tf.margin_bottom=0
    tf.vertical_anchor=MSO_ANCHOR.TOP
    for i,line in enumerate(lines):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.space_before=Pt(0);p.space_after=Pt(0);p.line_spacing=Pt(leading)
        r=p.add_run();r.text=line;r.font.name='DejaVu Sans Mono' if mono else 'Lato'
        r.font.size=Pt(size);r.font.bold=bold;r.font.color.rgb=rgb(c)
        if link:r.hyperlink.address=link
        pdf.setFont(font,size);pdf.setFillColorRGB(*color(c));pdf.drawString(x,H-y-size-i*leading,line)
    if link:pdf.linkURL(link,(x,H-y-h,x+w,H-y),relative=0,thickness=0)
    slides[-1]['text'].append(s)
    return box

def start(title,kicker='GROUP DISCUSSION',dark=False,source='',notes=''):
    global slide
    slide=prs.slides.add_slide(prs.slide_layouts[6])
    slides.append({'title':title,'notes':notes,'text':[]})
    slide.notes_slide.notes_text_frame.text=notes
    rect(0,0,W,H,NAVY if dark else BG)
    rect(42,33,28,4,TEAL if not dark else '72D3B9')
    text(kicker,82,26,820,22,11,'93BDB4' if dark else TEAL,True)
    if title:text(title,42,65,876,88,31,WHITE if dark else NAVY,True,leading=36)
    text('FASTA / CONTAMINANTS / PROJECT POLICY',42,511,550,18,9,'9EB1B9' if dark else MUTED)
    text(f'{len(slides):02d} / 12',857,509,65,20,11,'9EB1B9' if dark else MUTED)
    if source:text(source,42,484,870,22,10,'9EB1B9' if dark else MUTED)

def end():pdf.showPage()
def band(s,y=424,fill=MINT,c=TEAL):
    rect(42,y,876,48,fill,True);text(s,58,y+10,844,34,19,c,True)
def card(x,y,w,h,label,body,fill=WHITE,accent=TEAL):
    rect(x,y,w,h,fill,True)
    text(label,x+20,y+18,w-40,48,19,accent,True)
    text(body,x+20,y+73,w-40,h-80,19,INK)

start('',dark=True,kicker='CONTAMINANT DATABASES • A GROUP DECISION',notes='Purpose: agree on a database merge policy and a reproducible filtering policy. This deck advocates removing exact sequence redundancy while keeping biological identity and explicit project exceptions. It does not assert a measured FDR effect.')
text('Identical sequences.\nDifferent labels.',42,105,850,144,51,WHITE,True,leading=58)
text('What should a contaminant FASTA change?',45,271,830,45,28,'BDE5D7')
rect(44,353,870,1,'3C5360')
text('One sequence → one search record.\nProject policy decides what gets excluded.',45,380,800,75,24,WHITE,leading=32)
end()

start('The reported 117 drops are fully explained',source='[L] Local audit: Human_reviewed_20261106_20430entries_contaminant_tenzer.fasta',notes='Original input contained 20,430 human records and 169 Tenzer records. There were 117 extra records by accession: 116 cross-source collisions and one repeated P38507 within Tenzer. Every accession collision had an identical sequence. Header strings alone concealed most collisions.')
for x,value,label in [(42,'116','Human / contaminant\naccession collisions'),(340,'1','Repeated accession\ninside Tenzer'),(638,'117','Extra records\nwith duplicate IDs')]:
    rect(x,161,280,180,WHITE,True)
    text(value,x+20,174,240,80,61,TEAL,True)
    text(label,x+20,263,245,60,20,INK)
text('20,430 human + 169 contaminant records = 20,599 entries',45,363,870,35,23,INK)
band('All 117 accession-collision pairs have identical sequences.')
end()

start('A different name does not create a different ID',source='[1] DIA-NN documentation: accession parsing and default duplicate-ID handling.',notes='These are actual P02538 header tokens. The middle pipe-delimited field is the accession, and remains P02538 in both records. The CONTA suffix changes the protein name. Default DIA-NN behavior keeps the first record for a repeated ID. Renaming the accession would avoid an ID collision but would still leave sequence redundancy.')
text('UNDERLYING HUMAN DATABASE',58,153,820,22,12,MUTED,True)
rect(42,185,876,65,WHITE,True)
text('sp|',60,200,64,32,23,INK,mono=True)
rect(106,196,100,40,MINT,True)
text('P02538',113,202,95,30,20,TEAL,True,mono=True)
text('|K2C6A_HUMAN',212,200,650,35,23,INK,mono=True)
text('CONTAMINANT DATABASE',58,270,820,22,12,MUTED,True)
rect(42,302,876,65,WHITE,True)
text('sp|',60,317,64,32,23,INK,mono=True)
rect(106,313,100,40,MINT,True)
text('P02538',113,319,95,30,20,TEAL,True,mono=True)
text('|K2C6A_HUMAN_CONTA',212,317,650,35,23,INK,mono=True)
band('Changing the ID would fix parsing; identical peptide evidence remains.')
end()

start('Two labels cannot distinguish biological origin',source='Schematic reasoning: identical sequences yield the same peptide candidates under the same digestion settings.',notes='This is a statement about identifiability from sequence evidence, not about whether contamination is likely. The measured abundance can be a mixture of endogenous and exogenous molecules. Origin requires contextual evidence such as controls; a second database label cannot supply it.')
card(42,151,405,112,'Sample-derived keratin','',accent=TEAL)
card(513,151,405,112,'Handling-derived keratin','',accent=CORAL)
text('Same amino-acid sequence',104,210,300,30,19,INK)
text('Same amino-acid sequence',575,210,300,30,19,INK)
text('↘',295,274,95,60,34,TEAL,True)
text('↙',611,274,95,60,34,CORAL,True)
rect(227,329,506,71,NAVY,True)
text('One indistinguishable peptide evidence set',250,348,465,44,21,WHITE,True)
band('Origin may be sample, handling, or both. A suffix cannot resolve it.')
end()

start('The disagreement contains two separate questions',source='[2] Hao et al. discuss sample-specific contaminants and biological relevance of keratins.',notes='Both concerns are valid. Removing an exact sequence copy is a database representation decision. Excluding an identified sequence from downstream analysis is a project interpretation decision. Keeping two labels is not a substitute for specifying a filtering rule.')
card(42,155,425,242,'DATABASE REPRESENTATION','Why search two copies of an identical sequence?\n\nRetain one representative; preserve both sources and aliases.',accent=TEAL)
card(493,155,425,242,'BIOLOGICAL INTERPRETATION','Could this keratin be relevant to the sample?\n\nYes. Membership in a contaminant list is not proof of origin.',accent=CORAL)
band('Deduplication and exclusion need separate, explicit rules.')
end()

start('One search result can support different project policies',source='Illustrative policies only; each project must justify its own exclusions and exceptions.',notes='These are hypothetical examples, not a claim that every keratin should be excluded in a standard project or retained in an epithelial project. Both projects see the same identified sequence and contaminant-candidate annotation. Their saved policy differs. Retaining a candidate does not prove it is endogenous.')
text('Shared annotation: P02538 / KRT6A / common contaminant candidate',45,151,870,44,22,TEAL,True)
card(42,216,425,184,'PROJECT A','Handling keratins excluded.\nNo exception for P02538.\n\nOutcome: exclude from analysis.',accent=CORAL)
card(493,216,425,184,'PROJECT B','Keratin biology is in scope.\nP02538 explicitly allowlisted.\n\nOutcome: retain for analysis.',accent=TEAL)
band('Store the decision in project config; do not rely on memory.')
end()

start('Contaminant groups can make exceptions manageable',source='Proposed taxonomy. Groups may overlap; none establishes the origin of a particular detection.',notes='This grouping scheme is a proposal for the group to review, not an implemented or universal standard. A sequence may be a member of multiple groups. Accession overrides should take precedence over group exclusions, and the effective policy should be exported with results.')
rows=[('GROUP','EXAMPLES','POLICY QUESTION'),('Handling-associated','Human keratins','Relevant to this sample?'),('Reagent-associated','Trypsin; affinity reagents','Expected reagent background?'),('Culture-associated','Serum proteins','Present in culture conditions?'),('Standards / spike-ins','Added reference proteins','QC, quantification, or exclusion?')]
for i,(a,b,c) in enumerate(rows):
    y=154+i*55;rect(42,y,876,53,NAVY if i==0 else WHITE)
    for val,x,w in [(a,58,230),(b,300,270),(c,584,320)]:text(val,x,y+12,w,40,16,WHITE if i==0 else INK,bold=i==0)
end()

start('A merge policy must distinguish three cases',source='Proposed rules; sequence equality means full amino-acid sequence equality, not shared peptides alone.',notes='The first rule is the requested example: drop the human copy and retain the contaminant representative of an identical sequence. Alias mapping preserves all original identities, including identical sequences from different genes or loci. Same accession with different sequences requires distinct record identifiers or explicit review; choosing the longest is not generally justified.')
rows=[('INPUT RELATIONSHIP','RECOMMENDED ACTION'),('Same accession + same sequence','One representative; contaminants take priority.'),('Different accessions + same sequence','One sequence record; retain all aliases / genes.'),('Same accession + different sequences','Warn; preserve both with unambiguous IDs.')]
for i,(a,b) in enumerate(rows):
    y=158+i*64;rect(42,y,876,62,NAVY if i==0 else WHITE)
    text(a,58,y+14,365,48,17,WHITE if i==0 else INK,bold=i==0)
    text(b,435,y+14,465,48,17,WHITE if i==0 else INK,bold=i==0)
band('Do not collapse distinct sequences solely because IDs or lengths overlap.')
end()

start('Make the policy reproducible from FASTA to results',notes='This is a proposed end state. Keep downloaded source databases intact. Canonicalize identifiers for comparison without erasing their source labels. Save sequence-to-alias mapping and decisions. Apply a versioned project policy to retained identifications. The unmodified results should remain available for reanalysis.')
steps=[('01','SOURCE','Keep original\nFASTA files.'),('02','MERGE','Deduplicate exact\nsequence copies.'),('03','ANNOTATE','Save aliases, source,\ncandidate groups.'),('04','FILTER','Apply saved\nproject policy.')]
for i,(n,label,body) in enumerate(steps):
    x=42+i*223
    rect(x,164,207,213,WHITE,True)
    text(n,x+18,181,170,50,35,TEAL,True)
    text(label,x+18,247,172,29,17,NAVY,True)
    text(body,x+18,291,173,70,18,INK)
band('Deliver results + effective exclusion policy + merge / alias manifest.')
end()

start('FDR is a caveat, not the central argument',source='[1] DIA-NN documentation and issue #1140: grouping and representative selection depend on inference.',notes='No before/after search experiment in this work measured a change in protein FDR or identification sensitivity. Duplicate accessions and identical sequences are distinct issues. Inference software can select representatives or group redundant records; two entries need not be counted as two independent protein discoveries. Avoid asserting an inevitable or quantified FDR penalty.')
card(42,156,276,244,'ESTABLISHED','Exact copies add no distinct sequence evidence.\n\nDuplicate IDs trigger DIA-NN skipping.',accent=TEAL)
card(342,156,276,244,'TOOL-DEPENDENT','Two entries may be grouped or represented by one protein.\n\nTwo entries ≠ two independent findings.',accent=TEAL)
card(642,156,276,244,'NOT MEASURED','A change in FDR or sensitivity from these duplicates.\n\nRequires a controlled comparison.',fill=PALE,accent=CORAL)
band('Prefer the clarity argument; do not claim demonstrated FDR harm.')
end()

start('Current build: verified cleanup, remaining policy choices',source='[L] Local rerun, 12 Nov 2026: make succeeded; 42 downloads; 84 merged FASTAs verified.',notes='The current code removes duplicate accessions and sequences with contaminant priority and emits diagnostics. All 84 generated outputs were checked for unique IDs and sequences. Human reviewed plus Tenzer has 20,404 records after removing 195 records by combined deduplication. Warning categories overlap and must not be summed. Remaining work is explicitly proposed, not implemented by this deck.')
card(42,156,425,244,'VERIFIED IN CURRENT BUILD','84 outputs: unique IDs and sequences.\n\nHuman reviewed + Tenzer:\n20,599 → 20,404 records.\n\nDuplicate warnings include examples.',accent=TEAL)
card(493,156,425,244,'STILL TO AGREE / IMPLEMENT','Uniform Hao / Tenzer tagging.\n\nAlias and removal manifest.\n\nPreserve differing sequences.\n\nGroups + project filtering config.',fill=PALE,accent=CORAL)
band('Requested principle: contaminants win for identical sequence copies.')
end()

start('Evidence and discussion references',notes='Local audit files: duplicate_protein_ids_tenzer.tsv and warnings_summary_20261112.tsv in the repository root. Original 6 Nov accession-collision audit and 12 Nov rerun agree on the reviewed-human/Tenzer case. Source databases contain additional sequence duplicates unrelated to contaminants. The final policy in this deck is a proposal, not a claim of a universal standard.')
text('[L] Local database audit',45,151,870,30,22,TEAL,True)
text('Original 6 Nov 2026 FASTA: 117 extra accession records.\n12 Nov 2026 rerun: warning summary and 84-output uniqueness check.',45,190,870,65,19,INK)
text('[1] DIA-NN: identifier handling and protein inference',45,268,870,30,22,TEAL,True)
text('Documentation · default duplicate-ID handling',45,308,870,28,18,INK,link='https://github.com/vdemichev/DiaNN#command-line-reference')
text('Issue #1140 · identical sequences under different accessions',45,340,870,28,18,INK,link='https://github.com/vdemichev/DiaNN/issues/1140')
text('[2] Frankenfield et al., J. Proteome Res. (2022)',45,393,870,30,22,TEAL,True)
text('Protein Contaminants Matter · DOI: 10.1021/acs.jproteome.2c00145',45,432,870,28,18,INK,link='https://doi.org/10.1021/acs.jproteome.2c00145')
end()

assert len(slides)==12
if errors:raise RuntimeError(f'Text overflow: {errors}')
prs.save(OUT/'contaminant_duplicates.pptx');pdf.save()
(OUT/'speaker_notes.md').write_text('# Identical sequences, different labels\n\n'+'\n\n'.join(f'## {i}. {s["title"] or "Identical sequences. Different labels."}\n\n{s["notes"]}' for i,s in enumerate(slides,1)))
(OUT/'slide_text.json').write_text(json.dumps(slides,indent=2,ensure_ascii=False))
print(f'Created {len(slides)} slides: PowerPoint + PDF + speaker notes.')
