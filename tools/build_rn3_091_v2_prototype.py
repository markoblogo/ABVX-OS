#!/usr/bin/env python3
"""Build the human-gated RN3-091 V2 product-thesis prototype."""
from pathlib import Path
import json, re
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
V1=ROOT/'books/rn3-091'; BASE=V1/'v2'; DATA=BASE/'data'; QA=BASE/'qa'; PROTO=BASE/'prototype'
OUT=ROOT/'output/pdf/french-road-signs-for-ukrainian-drivers-v2-prototype.pdf'
for p in (DATA,QA,PROTO,OUT.parent): p.mkdir(parents=True,exist_ok=True)
W,H=8.5*inch,11*inch; M=48
INK=HexColor('#17212B'); BLUE=HexColor('#1557A0'); PALE=HexColor('#F2F5F7'); GOLD=HexColor('#D69A23'); RED=HexColor('#C83737'); GREEN=HexColor('#247A59'); GRAY=HexColor('#66717C')
pdfmetrics.registerFont(TTFont('Atlas','/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
pdfmetrics.registerFont(TTFont('Atlas-Bold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))

def wrap(c,text,x,y,width,size=10.5,leading=14,font='Atlas',color=INK,max_lines=20):
    c.setFont(font,size); c.setFillColor(color); words=text.split(); line=''; out=[]
    for word in words:
        trial=(line+' '+word).strip()
        if c.stringWidth(trial,font,size)<=width: line=trial
        else: out.append(line); line=word
    if line: out.append(line)
    for line in out[:max_lines]: c.drawString(x,y,line); y-=leading
    return y
def footer(c,n,label):
    c.setStrokeColor(HexColor('#DDE3E8')); c.line(M,34,W-M,34); c.setFont('Atlas',8); c.setFillColor(GRAY); c.drawString(M,20,label); c.drawRightString(W-M,20,str(n))
def title(c,kicker,head,dek=''):
    c.setFont('Atlas-Bold',8); c.setFillColor(BLUE); c.drawString(M,H-48,kicker.upper())
    y=wrap(c,head,M,H-79,W-2*M,25,29,'Atlas-Bold',INK,3)
    if dek: wrap(c,dek,M,y-8,W-2*M,11,15,'Atlas',GRAY,4)
def pill(c,x,y,text,color):
    c.setFillColor(color); c.roundRect(x,y,118,22,11,fill=1,stroke=0); c.setFillColor(white); c.setFont('Atlas-Bold',8); c.drawCentredString(x+59,y+7,text)
def fr_img(c,code,x,y,size):
    p=V1/'visuals/png'/f'{code}.png'; c.drawImage(str(p),x,y,size,size,preserveAspectRatio=True,anchor='c',mask='auto')
def ua_stop(c,x,y,s):
    c.setFillColor(RED); c.setStrokeColor(white); c.setLineWidth(s*.035)
    pts=[]
    import math
    for i in range(8):
        a=math.pi/8+i*math.pi/4; pts += [x+s/2+(s*.46)*math.cos(a),y+s/2+(s*.46)*math.sin(a)]
    path=c.beginPath(); path.moveTo(*pts[:2]); [path.lineTo(*pts[i:i+2]) for i in range(2,len(pts),2)]; path.close(); c.drawPath(path,fill=1,stroke=1)
    c.setFillColor(white); c.setFont('Atlas-Bold',s*.18); c.drawCentredString(x+s/2,y+s*.43,'STOP')
def ua_yield(c,x,y,s):
    c.setFillColor(white); c.setStrokeColor(RED); c.setLineWidth(s*.07); p=c.beginPath(); p.moveTo(x+s*.1,y+s*.88);p.lineTo(x+s*.9,y+s*.88);p.lineTo(x+s*.5,y+s*.12);p.close();c.drawPath(p,fill=1,stroke=1)
def ua_speed(c,x,y,s,num):
    c.setFillColor(white);c.setStrokeColor(RED);c.setLineWidth(s*.08);c.circle(x+s/2,y+s/2,s*.42,fill=1,stroke=1);c.setFillColor(INK);c.setFont('Atlas-Bold',s*.30);c.drawCentredString(x+s/2,y+s*.40,str(num))
def card(c,x,y,w,h,code,name,uk,cmp='MATCH',ua=None):
    c.setFillColor(PALE);c.roundRect(x,y,w,h,12,fill=1,stroke=0); fr_img(c,code,x+14,y+h-98,88)
    if ua: ua(c,x+w-68,y+h-72,48)
    colors={'MATCH':GREEN,'NEAR MATCH':GOLD,'DIFFERENT':RED,'NO ANALOGUE':GRAY}; pill(c,x+14,y+14,cmp,colors[cmp])
    c.setFillColor(BLUE);c.setFont('Atlas-Bold',8);c.drawString(x+112,y+h-31,code)
    yy=wrap(c,name,x+112,y+h-50,w-130,13,16,'Atlas-Bold',INK,2);wrap(c,uk,x+112,yy-5,w-130,9.5,13,'Atlas',INK,5)

c=Canvas(str(OUT),pagesize=(W,H)); c.setTitle('RN3-091 V2 prototype')
# 1
c.setFillColor(BLUE);c.rect(0,0,W,H,fill=1,stroke=0);c.setFillColor(white);c.setFont('Atlas-Bold',10);c.drawString(M,H-62,'RN3-091 · PRODUCT THESIS V2');wrap(c,'Французькі дорожні знаки для українських водіїв',M,H-130,W-2*M,31,35,'Atlas-Bold',white,4);wrap(c,'Що таке саме, що лише здається знайомим і що у Франції потрібно перевчити',M,H-285,W-2*M,15,21,'Atlas',white,4);c.setFillColor(HexColor('#EAF2FA'));c.roundRect(M,110,W-2*M,132,16,fill=1,stroke=0);wrap(c,'Ви вже знаєте українську дорожню систему. Ця книга не починає з нуля: вона використовує ваші знання як точку відліку і показує місця, де автоматичне перенесення звичок може підвести.',M+22,210,W-2*M-44,13,18,'Atlas-Bold',INK,6);footer(c,1,'Прототип V2');c.showPage()
# 2
title(c,'Частина I','Якщо ви вже водили в Україні','Ваше завдання — не вивчити дорогу заново, а відокремити безпечне перенесення досвіду від нових французьких правил.')
for i,(h,b,col) in enumerate([('ПЕРЕНЕСТИ','STOP, «Дати дорогу» та багато базових форм упізнаються майже без перекладу.',GREEN),('ПЕРЕВІРИТИ','Схожий знак може мати іншу зону дії, контекст або наслідки.',GOLD),('ПЕРЕВЧИТИ','Зони, пріоритет та контроль швидкості не можна зводити до візуальної схожості.',RED)]):
 y=H-245-i*145;c.setFillColor(PALE);c.roundRect(M,y,W-2*M,110,12,fill=1,stroke=0);c.setFillColor(col);c.rect(M,y,8,110,fill=1,stroke=0);c.setFillColor(INK);c.setFont('Atlas-Bold',14);c.drawString(M+28,y+76,h);wrap(c,b,M+28,y+55,W-2*M-55,11,15,'Atlas',INK,3)
footer(c,2,'Стартова карта');c.showPage()
#3
title(c,'Системна різниця','Не плутайте знак, правило і практику','Знак — лише видима частина системи. Рішення водія залежить також від загального правила, розмітки, світлофора і локальної організації руху.')
steps=[('1','ЩО БАЧУ','форма, колір, символ, число'),('2','ЯКЕ ПРАВИЛО','національне правило та знак'),('3','ДЕ ДІЄ','точка, ділянка, зона, перехрестя'),('4','ЩО РОБЛЮ','сповільнююся, поступаюся, зупиняюся')]
for i,(n,h,b) in enumerate(steps):
 y=H-225-i*112;c.setFillColor(PALE);c.roundRect(M,y,W-2*M,82,12,fill=1,stroke=0);c.setFillColor(BLUE);c.circle(M+34,y+41,20,fill=1,stroke=0);c.setFillColor(white);c.setFont('Atlas-Bold',13);c.drawCentredString(M+34,y+36,n);c.setFillColor(INK);c.setFont('Atlas-Bold',11);c.drawString(M+70,y+50,h);c.setFont('Atlas',10);c.drawString(M+70,y+29,b)
footer(c,3,'Система перед словником');c.showPage()
#4 speed
title(c,'Ключова різниця','Швидкість: ліміт не дорівнює «допуску»','Порівнюйте правову межу, технічну поправку вимірювання і поріг відповідальності окремо.')
for x,h,col in [(M,'ФРАНЦІЯ',BLUE),(W/2+8,'УКРАЇНА',HexColor('#2867B2'))]:
 c.setFillColor(col);c.roundRect(x,H-275,W/2-M-16,122,12,fill=1,stroke=0);c.setFillColor(white);c.setFont('Atlas-Bold',16);c.drawString(x+18,H-190,h)
 if h=='ФРАНЦІЯ': wrap(c,'Для стаціонарного радара з виміряної швидкості віднімають 5 км/год до 100 км/год або 5% понад 100. Санкція прив’язана до «утриманої» швидкості, що перевищує ліміт.',x+18,H-218,W/2-M-52,9.4,13,'Atlas',white,6)
 else: wrap(c,'Знак 3.29 забороняє перевищувати вказану швидкість. Стаття 122 КУпАП встановлює відповідальність за перевищення більш як на 20 км/год; це не дозволений запас швидкості.',x+18,H-218,W/2-M-52,9.4,13,'Atlas',white,6)
c.setFillColor(PALE);c.roundRect(M,H-475,W-2*M,145,12,fill=1,stroke=0);c.setFillColor(INK);c.setFont('Atlas-Bold',14);c.drawString(M+22,H-365,'Практичний висновок');wrap(c,'Не переносіть український поріг адміністративної відповідальності у Францію як «звичні +20». І не сприймайте французьку технічну поправку радара як дозвіл їхати швидше: законний орієнтир — число на знаку або чинний загальний ліміт.',M+22,H-392,W-2*M-44,11,16,'Atlas',INK,6)
wrap(c,'Джерела: Code de la route R413-2; Sécurité routière, brochure radars (2025); ПДР України, п. 12 та знак 3.29; КУпАП, ст. 122. Перевірено 06.09.2026.',M,H-545,W-2*M,8.5,12,'Atlas',GRAY,4);footer(c,4,'Порівняння швидкості');c.showPage()
#5
title(c,'Частина II','Як читати французький знак','Спочатку сімейство, потім символ і лише тоді — деталі та додаткові таблички.')
families=[('warning','НЕБЕЗПЕКА','попередження — підготуйтеся'),('ban','ЗАБОРОНА','червоне кільце обмежує'),('must','ОБОВ’ЯЗОК','синє коло задає дію'),('info','ІНФОРМАЦІЯ / ЗОНА','контекст і межі дії')]
for i,(shape,h,b) in enumerate(families):
 x=M+(i%2)*(W/2-M+4); y=H-270-(i//2)*190;c.setFillColor(PALE);c.roundRect(x,y,W/2-M-12,150,12,fill=1,stroke=0)
 cx,cy=x+48,y+91;c.setLineWidth(5)
 if shape=='warning':
  c.setStrokeColor(RED);c.setFillColor(white);p=c.beginPath();p.moveTo(cx,cy+29);p.lineTo(cx-28,cy-23);p.lineTo(cx+28,cy-23);p.close();c.drawPath(p,fill=1,stroke=1)
 elif shape=='ban': c.setStrokeColor(RED);c.setFillColor(white);c.circle(cx,cy,27,fill=1,stroke=1)
 elif shape=='must': c.setFillColor(BLUE);c.setStrokeColor(BLUE);c.circle(cx,cy,28,fill=1,stroke=0)
 else: c.setFillColor(BLUE);c.setStrokeColor(BLUE);c.roundRect(cx-28,cy-25,56,50,4,fill=1,stroke=0)
 c.setFillColor(INK);c.setFont('Atlas-Bold',11);c.drawString(x+92,y+105,h);wrap(c,b,x+92,y+80,W/2-M-115,10,14,'Atlas',INK,4)
footer(c,5,'Візуальна граматика');c.showPage()
#6 two-up
title(c,'Атлас · два знаки','Зупинка і поступка');card(c,M,H-385,W-2*M,130,'AB4','Arrêt à l’intersection','Повна зупинка, потім дати дорогу. Українська точка опори: знак 2.2.', 'MATCH',ua_stop);card(c,M,H-545,W-2*M,130,'AB3a','Cédez le passage','Сповільніться і дайте дорогу. Українська точка опори: знак 2.1.','MATCH',ua_yield);footer(c,6,'Два пов’язані знаки');c.showPage()
#7 four-up
title(c,'Атлас · чотири знаки','Сімейство швидкості','Число читається легко; важче — зрозуміти, чи це точкове обмеження, зона або кінець режиму.')
for i,(code,name,uk) in enumerate([('B14_30','Limitation 30','Максимум 30 від знака'),('B14_50','Limitation 50','Максимум 50 від знака'),('B33_30','Fin de limitation 30','Кінець обмеження 30'),('B30','Zone 30','Початок зонального режиму')]):
 x=M+(i%2)*(W/2-M+4);y=H-360-(i//2)*230;card(c,x,y,W/2-M-12,190,code,name,uk,'NEAR MATCH')
footer(c,7,'Сімейна карта');c.showPage()
#8 MATCH
title(c,'Порівняння · MATCH','= Майже так само: STOP','Форма, напис і основна дія безпечно переносяться з українського досвіду.')
fr_img(c,'AB4',M+25,H-410,185);ua_stop(c,W-220,H-355,115);pill(c,W/2-59,H-455,'MATCH',GREEN);wrap(c,'Франція AB4: повністю зупинитися на межі дороги, на яку виїжджаєте, потім дати дорогу й рушати лише безпечно.',M,H-510,W-2*M,12,17,'Atlas-Bold',INK,4);wrap(c,'Україна 2.2: проїзд без зупинки заборонено перед стоп-лінією, а за її відсутності — перед знаком; далі потрібно дати дорогу.',M,H-590,W-2*M,11,16,'Atlas',INK,5);footer(c,8,'Безпечне перенесення');c.showPage()
#9 near
title(c,'Порівняння · NEAR MATCH','≈ Знак знайомий, система контролю — ні');fr_img(c,'B14_50',M+30,H-390,170);ua_speed(c,W-215,H-345,110,50);pill(c,W/2-59,H-445,'NEAR MATCH',GOLD);wrap(c,'Обидва знаки встановлюють максимальну швидкість 50 км/год. Візуальна й основна правова функція близькі.',M,H-500,W-2*M,12,17,'Atlas-Bold',INK,3);wrap(c,'Важлива різниця не в колі з числом, а в тому, як фіксується і санкціонується перевищення. Саме тому ця пара — не MATCH для практичного перенесення звички.',M,H-575,W-2*M,11,16,'Atlas',INK,5);footer(c,9,'Схоже, але перевірити');c.showPage()
#10 different
title(c,'Порівняння · DIFFERENT SYSTEM','≠ Пріоритет праворуч: знак не створює правило');fr_img(c,'AB1',M+25,H-400,175);c.setFillColor(PALE);c.roundRect(W-250,H-370,190,120,12,fill=1,stroke=0);c.setFillColor(INK);c.setFont('Atlas-Bold',12);c.drawString(W-230,H-292,'Україна · 1.21');wrap(c,'Попередження про перехрестя рівнозначних доріг.',W-230,H-316,150,10,14,'Atlas',INK,4);pill(c,W/2-59,H-450,'DIFFERENT',RED);wrap(c,'У Франції загальне правило на нерегульованому перехресті — поступитися транспортові праворуч, якщо інше не встановлено. AB1 попереджає, що це правило застосовується попереду.',M,H-510,W-2*M,11,16,'Atlas-Bold',INK,5);wrap(c,'В Україні на перехресті рівнозначних доріг також поступаються транспортові праворуч, а знак 1.21 попереджає про таке перехрестя. Практична пастка — очікувати, що у Франції право проїзду завжди буде явно позначене знаком.',M,H-600,W-2*M,10.5,15,'Atlas',INK,6);footer(c,10,'Одна ситуація, інша увага');c.showPage()
#11 no analogue
title(c,'Порівняння · NO DIRECT ANALOGUE','Ø Zone de rencontre — окремий французький режим');fr_img(c,'B52',M+20,H-405,185);pill(c,W/2-59,H-450,'NO ANALOGUE',GRAY);wrap(c,'У зоні зустрічі пішоходи можуть рухатися проїзною частиною і мають пріоритет перед транспортом; максимальна швидкість — 20 км/год. Для велосипедистів типовим є двосторонній рух, якщо місцеве рішення не встановило інше.',M,H-505,W-2*M,11,16,'Atlas-Bold',INK,6);wrap(c,'Українська «житлова зона» — корисна асоціація, але не прямий юридичний аналог. Не переносіть назву чи повний набір правил автоматично.',M,H-620,W-2*M,11,16,'Atlas',INK,4);wrap(c,'Джерело Франції: Code de la route R110-2. Українська точка порівняння: ПДР, знак 5.34 та розділ 26.',M,H-700,W-2*M,8.5,12,'Atlas',GRAY,3);footer(c,11,'Новий режим');c.showPage()
#12 high value
title(c,'Висока цінність','Коли знайома форма створює хибну впевненість')
for i,(h,b,col) in enumerate([('1. УПІЗНАВ','Так, форма й базове повідомлення знайомі.',GREEN),('2. ПЕРЕВІРИВ','Чи однакові зона дії, винятки та контекст?',GOLD),('3. ЗМІНИВ ДІЮ','Якщо система інша — не покладаюся на стару звичку.',RED)]):
 y=H-245-i*135;c.setFillColor(PALE);c.roundRect(M,y,W-2*M,100,12,fill=1,stroke=0);c.setFillColor(col);c.rect(M,y,8,100,fill=1,stroke=0);c.setFillColor(INK);c.setFont('Atlas-Bold',14);c.drawString(M+26,y+66,h);wrap(c,b,M+26,y+43,W-2*M-50,10.5,14,'Atlas',INK,3)
wrap(c,'Це і є робоча модель книги: не перекладати очевидне, а знаходити момент, де знайомство перестає бути достатнім.',M,H-670,W-2*M,13,18,'Atlas-Bold',BLUE,4);footer(c,12,'Перенесення без пасток');c.showPage()
#13 review
title(c,'Швидкий повтор','Що переносимо, що перевіряємо?','Закрийте підписи. Назвіть дію і стан порівняння.')
for i,(code,label) in enumerate([('AB4','STOP'),('AB3a','Дати дорогу'),('B14_50','50 км/год'),('AB1','Пріоритет праворуч'),('B52','Zone de rencontre'),('B30','Zone 30')]):
 x=M+(i%3)*170;y=H-300-(i//3)*235;fr_img(c,code,x+15,y,110);c.setFillColor(PALE);c.roundRect(x,y-42,140,30,8,fill=1,stroke=0);c.setFillColor(INK);c.setFont('Atlas-Bold',8.5);c.drawCentredString(x+70,y-31,label)
wrap(c,'Відповіді: AB4 — MATCH; AB3a — MATCH; B14 — NEAR MATCH для практики контролю; AB1 — DIFFERENT SYSTEM; B52 — NO DIRECT ANALOGUE; B30 — перевірити зональну дію.',M,92,W-2*M,8.5,12,'Atlas',GRAY,4);footer(c,13,'Активне пригадування');c.showPage()
#14 index
title(c,'Пошук','Двомовний покажчик · зразок','У повній книзі терміни, українські поняття і коди знаків ведуть на сторінки та Kindle-якорі.')
items=[('arrêt','зупинка','AB4'),('cédez le passage','дати дорогу','AB3a'),('limitation de vitesse','обмеження швидкості','B14'),('priorité à droite','перевага праворуч','AB1'),('zone de rencontre','зона зустрічі','B52'),('zone 30','зона 30','B30')]
y=H-190
for fr,uk,code in items:
 c.setFillColor(PALE);c.roundRect(M,y-42,W-2*M,54,8,fill=1,stroke=0);c.setFillColor(BLUE);c.setFont('Atlas-Bold',11);c.drawString(M+16,y-10,fr);c.setFillColor(INK);c.setFont('Atlas',10);c.drawString(M+230,y-10,uk);c.setFont('Atlas-Bold',10);c.drawRightString(W-M-16,y-10,code);y-=70
wrap(c,'Незалежний навчальний посібник; не є офіційним виданням і не замінює чинні правила Франції або України.',M,80,W-2*M,8.5,12,'Atlas',GRAY,3);footer(c,14,'Навігаційний шар');c.showPage();c.save()

reader=PdfReader(str(OUT)); text='\n'.join((p.extract_text() or '') for p in reader.pages)
report={"schema_version":"rn3-091-v2-prototype-qa/v1","status":"PASS" if len(reader.pages)==14 and 'Ø Zone de rencontre' in text else "FAIL","pages":len(reader.pages),"word_count":len(re.findall(r"\b[\wÀ-ÿА-Яа-яІіЇїЄє’'-]+\b",text)),"required_archetypes":["opening","system_difference","speed_enforcement","sign_primer","two_up","four_up","match","near_match","different_system","no_direct_analogue","high_value_difference","quick_review","vocabulary_index"],"artifact":str(OUT.relative_to(ROOT)),"human_gate":"PENDING"}
(QA/'prototype-technical-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
