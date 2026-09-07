#!/usr/bin/env python3
"""Eight normal-book pages for RN3-091 V2 human product gate #2."""
from pathlib import Path
import json, math, re
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'books/rn3-091'; V2=BASE/'v2'
OUT=ROOT/'output/pdf/french-road-signs-for-ukrainian-drivers-v2-gate2-prototype.pdf'; OUT.parent.mkdir(parents=True,exist_ok=True)
W,H=8.5*inch,11*inch; M=44; G=17; CW=(W-2*M-G)/2
INK=HexColor('#18232D'); BLUE=HexColor('#165A9F'); PALE=HexColor('#F1F4F6'); LINE=HexColor('#D7DFE5'); RED=HexColor('#C93636'); GREEN=HexColor('#287A58'); GOLD=HexColor('#B77A0B'); GRAY=HexColor('#65717C')
pdfmetrics.registerFont(TTFont('Atlas','/System/Library/Fonts/Supplemental/Arial Unicode.ttf'));pdfmetrics.registerFont(TTFont('Atlas-Bold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
BODY=ParagraphStyle('body',fontName='Atlas',fontSize=10.8,leading=14.7,textColor=INK,spaceAfter=6.5); SMALL=ParagraphStyle('small',parent=BODY,fontSize=8.8,leading=11.7,spaceAfter=4.5)

def para(c,text,x,y,w,style=BODY):
 q=Paragraph(text,style);_,h=q.wrap(w,H);q.drawOn(c,x,y-h);return y-h-style.spaceAfter
def page_head(c,kicker,title,deck=''):
 c.setFillColor(BLUE);c.setFont('Atlas-Bold',7.8);c.drawString(M,H-36,kicker.upper());c.setFillColor(INK);c.setFont('Atlas-Bold',20);c.drawString(M,H-63,title);y=H-82
 if deck:y=para(c,deck,M,y,W-2*M,ParagraphStyle('deck',parent=BODY,fontSize=9.6,leading=12.6,textColor=GRAY))
 c.setStrokeColor(LINE);c.line(M,y-1,W-M,y-1);return y-14
def foot(c,n,label):
 c.setStrokeColor(LINE);c.line(M,28,W-M,28);c.setFillColor(GRAY);c.setFont('Atlas',7);c.drawString(M,15,label);c.drawRightString(W-M,15,str(n))
def sub(c,text,x,y):c.setFillColor(INK);c.setFont('Atlas-Bold',12);c.drawString(x,y,text);return y-19
def note(c,title,text,x,y,w,color=BLUE):
 q=Paragraph(text,SMALL);_,th=q.wrap(w-22,H);h=th+30;c.setFillColor(PALE);c.roundRect(x,y-h,w,h,6,fill=1,stroke=0);c.setFillColor(color);c.rect(x,y-h,4,h,fill=1,stroke=0);c.setFont('Atlas-Bold',7.7);c.drawString(x+11,y-13,title);q.drawOn(c,x+11,y-h+8);return y-h-7
def img(c,code,x,y,s):c.drawImage(str(BASE/'visuals/png'/f'{code}.png'),x,y,s,s,preserveAspectRatio=True,anchor='c',mask='auto')
def ua_stop(c,x,y,s):
 pts=[]
 for i in range(8):a=math.pi/8+i*math.pi/4;pts += [x+s/2+s*.46*math.cos(a),y+s/2+s*.46*math.sin(a)]
 c.setFillColor(RED);c.setStrokeColor(white);c.setLineWidth(2);p=c.beginPath();p.moveTo(*pts[:2]);[p.lineTo(*pts[i:i+2]) for i in range(2,len(pts),2)];p.close();c.drawPath(p,fill=1,stroke=1);c.setFillColor(white);c.setFont('Atlas-Bold',s*.17);c.drawCentredString(x+s/2,y+s*.43,'STOP')
def ua_yield(c,x,y,s):
 c.setFillColor(white);c.setStrokeColor(RED);c.setLineWidth(s*.07);p=c.beginPath();p.moveTo(x+s*.1,y+s*.88);p.lineTo(x+s*.9,y+s*.88);p.lineTo(x+s*.5,y+s*.12);p.close();c.drawPath(p,fill=1,stroke=1)
def ua_speed(c,x,y,s,n):c.setFillColor(white);c.setStrokeColor(RED);c.setLineWidth(s*.08);c.circle(x+s/2,y+s/2,s*.42,fill=1,stroke=1);c.setFillColor(INK);c.setFont('Atlas-Bold',s*.28);c.drawCentredString(x+s/2,y+s*.4,str(n))
LABELS={'MATCH':('Збігається',GREEN),'NEAR_MATCH':('Схожий, але є різниця',GOLD),'DIFFERENT_SYSTEM':('В Україні інакше',RED),'NO_DIRECT_ANALOGUE':('Прямого аналога немає',GRAY)}
def badge(c,state,x,y,w=126):
 text,col=LABELS[state];c.setFillColor(col);c.roundRect(x,y,w,16,8,fill=1,stroke=0);c.setFillColor(white);c.setFont('Atlas-Bold',6.4);c.drawCentredString(x+w/2,y+5,text)
def entry(c,x,y,w,h,code,fr,uk,action,state,ua=None,trap='',comparison=''):
 c.setFillColor(white);c.setStrokeColor(LINE);c.roundRect(x,y,w,h,7,fill=1,stroke=1);img(c,code,x+9,y+h-126,108);c.setFillColor(BLUE);c.setFont('Atlas-Bold',7.8);c.drawString(x+132,y+h-21,code)
 yy=para(c,f'<b>{fr}</b>',x+132,y+h-31,w-144,ParagraphStyle('fr',parent=BODY,fontSize=11.2,leading=13.4));yy=para(c,uk,x+132,yy,w-144,SMALL);yy=para(c,f'<b>На практиці.</b> {action}',x+132,yy,w-144,SMALL)
 if comparison: para(c,f'<b>Порівняння.</b> {comparison}',x+132,y+96,w-144,SMALL)
 badge(c,state,x+11,y+11)
 if ua:ua(c,x+w-51,y+12,35)
 if trap:para(c,f'<b>Пастка:</b> {trap}',x+145,y+27,w-157,ParagraphStyle('trap',parent=SMALL,fontSize=7.2,leading=9.3,textColor=RED))

c=Canvas(str(OUT),pagesize=(W,H));c.setTitle('RN3-091 V2 Gate 2 prototype')
# 1 prose
y=page_head(c,'Ключові відмінності правил дорожнього руху у Франції та Україні','Швидкість: знак, вимірювання, санкція','Розділ пояснює французьке правило з нуля, а потім показує, що саме не можна автоматично переносити з українського досвіду.')
x=M; a=sub(c,'Який ліміт діє у Франції',x,y);a=para(c,'Для легкового автомобіля загальні максимуми залежать від дороги: 130 км/год на автомагістралі, 110 на дорозі з розділеними напрямками та 80 на інших дорогах поза населеними пунктами, якщо знак або уповноважений орган не встановив інше. Під час дощу частина максимумів знижується. Конкретний знак завжди важливіший за «типове» число, яке ви пам’ятаєте.',x,a,CW)
a=sub(c,'Три величини, а не одна',x,a);a=para(c,'Законний ліміт — це швидкість, яку не можна перевищувати. Виміряна швидкість — показання приладу. Утримана швидкість — результат після нормативної технічної поправки, який використовують у провадженні. Для французького стаціонарного радара від виміряної швидкості віднімають 5 км/год до 100 км/год або 5% понад 100 км/год.',x,a,CW)
a=note(c,'ВАЖЛИВО','Технічна поправка враховує похибку приладу. Вона не є дозволом додати 5 км/год до знака.',x,a,CW,RED)
x=M+CW+G; b=sub(c,'Що означає український поріг',x,y);b=para(c,'Український знак 3.29 так само забороняє рух швидше числа на знаку. Окремо стаття 122 КУпАП встановлює відповідальність за перевищення більш як на 20 км/год та вищий рівень за перевищення більш як на 50 км/год. Це пороги адміністративної відповідальності, а не додаток до дозволеної швидкості.',x,b,CW)
b=sub(c,'Практичне порівняння',x,b);b=para(c,'Якщо знак показує 50, правильний орієнтир в обох країнах — не більше 50. Відмінність починається у процедурі вимірювання та санкціонування. Тому українське уявлення про «+20» не можна переносити у Францію, а французьку поправку радара не можна перетворювати на особистий запас.',x,b,CW)
b=sub(c,'Перед виїздом',x,b);b=para(c,'Перевірте погоду, конкретні знаки та місцево встановлені обмеження. У складній ситуації знижуйте швидкість нижче максимуму: французьке правило окремо вимагає пристосовувати її до стану дороги, видимості та руху.',x,b,CW)
b=note(c,'ДЛЯ НОВОГО ВОДІЯ','Спочатку вивчіть французьке правило. Порівняння з Україною — додаткове пояснення, а не передумова.',x,b,CW)
para(c,'Джерела: Code de la route R413-2, R413-17; Sécurité routière, матеріали про радари; ПДР України, знак 3.29; КУпАП, ст. 122. Перевірено 07.09.2026.',M,48,W-2*M,ParagraphStyle('src1',parent=SMALL,fontSize=6.5,leading=7.7,textColor=GRAY));foot(c,1,'Ключові відмінності');c.showPage()
# 2 prose
y=page_head(c,'Ключові відмінності правил дорожнього руху у Франції та Україні','Пріоритет, кільця, телефон і міські зони')
x=M;a=sub(c,'Пріоритет праворуч',x,y);a=para(c,'У Франції на перехресті без іншого регулювання водій, який наближається зліва, поступається водієві праворуч. Знак AB1 лише попереджає, що це правило застосовується попереду; він не створює правило. В Україні на рівнозначному нерегульованому перехресті також поступаються транспортові праворуч. Практична пастка у Франції — чекати окремого знака перед кожним таким перехрестям.',x,a,CW)
a=sub(c,'Круговий рух',x,a);a=para(c,'На французькому carrefour à sens giratoire водій при в’їзді поступається тим, хто вже рухається кільцем. В Україні на нерегульованому перехресті з круговим рухом, позначеному знаком 4.10, перевагу також мають транспортні засоби на колі. Але смуги, стрілки, світлофор і знаки конкретного перехрестя залишаються обов’язковими.',x,a,CW)
a=note(c,'НЕ ВГАДУЙТЕ ЗА ФОРМОЮ','Коло в плані дороги ще не пояснює весь режим. Спочатку визначте знаки пріоритету та розмітку.',x,a,CW,GOLD)
x=M+CW+G;b=sub(c,'Телефон і навушники',x,y);b=para(c,'В обох країнах під час руху не можна користуватися телефоном, тримаючи його в руці. Французьке правило додатково прямо забороняє водієві носити у вусі пристрій, здатний відтворювати звук, крім слухового апарата та передбачених вузьких винятків. Один навушник або звичайна гарнітура не є безпечним обхідним шляхом.',x,b,CW)
b=sub(c,'Zone 30 і zone de rencontre',x,b);b=para(c,'Це зональні режими, а не одиничні команди біля одного стовпа. У zone de rencontre максимум становить 20 км/год; пішоходи можуть рухатися проїзною частиною і мають пріоритет. Дія режиму триває до позначеного виходу із зони.',x,b,CW)
b=sub(c,'Екологічні обмеження',x,b);b=para(c,'У Франції існують місцеві зони низьких викидів — ZFE — та ідентифікація Crit’Air. Конкретні межі, категорії допуску й винятки залежать від території та можуть змінюватися. Тому книга пояснює систему, але перед поїздкою водій перевіряє актуальні правила потрібного міста.',x,b,CW)
b=note(c,'НАЦІОНАЛЬНЕ ≠ МІСЦЕВЕ','Не переносіть правило Парижа, Ліона чи іншої агломерації на всю Францію.',x,b,CW)
para(c,'Джерела: Code de la route R110-2, R412-6-1, R415-5, R415-10; ПДР України 2.9, 16.12; офіційна інформація Crit’Air/ZFE.',M,48,W-2*M,ParagraphStyle('src2',parent=SMALL,fontSize=6.5,leading=7.7,textColor=GRAY));foot(c,2,'Ключові відмінності');c.showPage()
# 3 dense primer
y=page_head(c,'Як читати французькі знаки','Візуальна граматика на одній сторінці','Алгоритм працює і для першого знайомства, і для перевірки вже знайомого знака.')
cards=[('ТРИКУТНИК','Небезпека','Попереджає, що попереду потрібна додаткова увага. Символ називає ризик; сам трикутник не задає швидкість.'),('ЧЕРВОНЕ КОЛО','Заборона','Обмежує в’їзд, маневр, категорію транспорту або швидкість. Число й символ визначають конкретну команду.'),('СИНЄ КОЛО','Обов’язкова дія','Задає напрямок, шлях або іншу обов’язкову поведінку. Це не просто рекомендація.'),('КВАДРАТ / ПРЯМОКУТНИК','Інформація або режим','Позначає дорогу, сервіс, смугу, початок зони чи особливий режим. Значення залежить від повної композиції.')]
for i,(shape,h,t) in enumerate(cards):
 xx=M+(i%2)*(CW+G);yy=y-(i//2)*134;c.setFillColor(PALE);c.roundRect(xx,yy-112,CW,105,6,fill=1,stroke=0);c.setFillColor(BLUE);c.setFont('Atlas-Bold',6.8);c.drawString(xx+11,yy-24,shape);c.setFillColor(INK);c.setFont('Atlas-Bold',10);c.drawString(xx+11,yy-43,h);para(c,t,xx+11,yy-51,CW-22,SMALL)
yy=y-285;yy=sub(c,'Перед тим як діяти, перевірте три уточнення',M,yy)
for i,(h,t) in enumerate([('Символ або число','Що саме заборонено, наказано або очікується?'),('Додаткова табличка','Кому, де, коли й на якій відстані діє повідомлення?'),('Початок і кінець','Це точковий знак, ділянка чи зональний режим?')]):
 xx=M+i*((W-2*M-2*G)/3+G);ww=(W-2*M-2*G)/3;c.setStrokeColor(LINE);c.roundRect(xx,yy-80,ww,73,5,fill=0,stroke=1);c.setFillColor(INK);c.setFont('Atlas-Bold',8);c.drawString(xx+9,yy-26,h);para(c,t,xx+9,yy-34,ww-18,ParagraphStyle('mini',parent=SMALL,fontSize=7.1,leading=9.2))
note(c,'РОБОЧИЙ АЛГОРИТМ','1) Назвіть сімейство. 2) Прочитайте символ або число. 3) Перевірте табличку й межі дії. 4) Визначте практичну дію. 5) Лише потім порівнюйте з українським аналогом.',M,165,W-2*M,BLUE);foot(c,3,'Візуальна граматика');c.showPage()
# 4 two entries
y=page_head(c,'Атлас: пріоритет','STOP і «Дати дорогу»','Французький знак — головний. Менший український знак з’являється лише там, де справді допомагає розпізнаванню.')
entry(c,M,y-244,W-2*M,230,'AB4','Arrêt à l’intersection','STOP: обов’язкова повна зупинка.','Зупиніться на межі дороги, дайте дорогу та в’їжджайте лише коли це безпечно.','MATCH',ua_stop,'Дуже повільний проїзд не замінює зупинку.','Форма й базова дія збігаються з українським знаком 2.2. Відмінність шукайте не в символі, а в конкретній лінії зупинки та видимості на перехресті.')
entry(c,M,y-482,W-2*M,230,'AB3a','Cédez le passage','Дати дорогу.','Зменште швидкість і пропустіть тих, хто має пріоритет. Повна зупинка потрібна, якщо без неї неможливо безпечно поступитися.','MATCH',ua_yield,'Не плутайте із STOP: вимога поступитися однакова, вимога повної зупинки — ні.','Український знак 2.1 дуже близький за формою і значенням. Знайомий силует допомагає впізнати команду, але не визначає, кому саме належить пріоритет.')
foot(c,4,'Атлас · пріоритет');c.showPage()
# 5 two entries
y=page_head(c,'Атлас: перехрестя','Праворуч і по колу','Знайомий принцип не скасовує потреби прочитати французький контекст.')
entry(c,M,y-244,W-2*M,230,'AB1','Priorité à droite','Попереду діє пріоритет праворуч.','Завчасно знизьте швидкість і контролюйте транспорт праворуч. Загальне правило може діяти і без знака AB1.','DIFFERENT_SYSTEM',None,'Не чекайте знака «головна дорога» на кожному міському перехресті.','Правило перешкоди праворуч знайоме й в Україні, але французький попереджувальний знак має іншу візуальну роль. Учіть не лише картинку, а й умову застосування правила.')
entry(c,M,y-482,W-2*M,230,'AB25','Carrefour à sens giratoire','Перед в’їздом на кільце дайте дорогу.','Пропустіть тих, хто вже рухається кільцем; далі обирайте смугу і вихід за знаками та розміткою.','NEAR_MATCH',None,'Кругла форма перехрестя не скасовує локальних смуг, стрілок або світлофора.','Базова дія близька до українського кільця зі знаком 4.10: транспорт на колі має перевагу. Французька комбінація знаків і конкретна розмітка залишаються вирішальними.')
foot(c,5,'Атлас · перехрестя');c.showPage()
# 6 four entries
y=page_head(c,'Атлас: швидкість і зони','Одна цифра — різна зона дії')
items=[('B14_30','Limitation à 30','Максимум 30 від місця знака.','Читайте число як межу, а не рекомендовану швидкість.','NEAR_MATCH'),('B30','Entrée d’une zone 30','Початок зонального режиму 30.','Режим охоплює вулиці зони до позначеного виходу.','NEAR_MATCH'),('B33_30','Fin de limitation à 30','Кінець обмеження 30.','Після знака перевірте загальний або наступний ліміт.','MATCH'),('B52','Entrée d’une zone de rencontre','Зона 20 з пріоритетом пішоходів.','Очікуйте людей на проїзній частині; максимум — 20.','NO_DIRECT_ANALOGUE')]
for i,(code,fr,uk,action,state) in enumerate(items):
 xx=M+(i%2)*(CW+G);yy=y-(i//2)*232;c.setStrokeColor(LINE);c.roundRect(xx,yy-211,CW,202,6,fill=0,stroke=1);img(c,code,xx+10,yy-114,88);c.setFillColor(BLUE);c.setFont('Atlas-Bold',6.8);c.drawString(xx+112,yy-28,code);q=para(c,f'<b>{fr}</b>',xx+112,yy-37,CW-124,ParagraphStyle('fourfr',parent=SMALL,fontSize=8.6,leading=10.4));q=para(c,uk,xx+112,q,CW-124,ParagraphStyle('fouruk',parent=SMALL,fontSize=7.2,leading=9.2));para(c,f'<b>Дія.</b> {action}',xx+112,q,CW-124,ParagraphStyle('fouract',parent=SMALL,fontSize=7.2,leading=9.2));badge(c,state,xx+10,yy-194,134)
foot(c,6,'Атлас · чотири знаки');c.showPage()
# 7 comparison
y=page_head(c,'Важливе порівняння','50 означає 50 в обох країнах','Відмінність — не у знаку, а у вимірюванні та правозастосуванні.')
img(c,'B14_50',M,y-154,125);ua_speed(c,W-M-76,y-112,68,50);badge(c,'NEAR_MATCH',W/2-72,y-145,144)
yy=y-180; cols=[('1. ЗАКОННИЙ ЛІМІТ','Франція: B14 забороняє перевищувати показане число. Україна: знак 3.29 робить те саме. Тут значення майже збігається.'),('2. ВИМІРЮВАННЯ','Франція: для стаціонарного радара застосовують технічну поправку 5 км/год до 100 або 5% понад 100. Так отримують утриману швидкість.'),('3. ВІДПОВІДАЛЬНІСТЬ','Україна: стаття 122 КУпАП окремо називає перевищення більш як на 20 км/год. Це не змінює знак і не створює дозволеного запасу.')]
for i,(h,t) in enumerate(cols):
 xx=M+i*((W-2*M-2*G)/3+G);ww=(W-2*M-2*G)/3;c.setFillColor(PALE);c.roundRect(xx,yy-158,ww,149,6,fill=1,stroke=0);c.setFillColor(INK);c.setFont('Atlas-Bold',7.8);c.drawString(xx+10,yy-27,h);para(c,t,xx+10,yy-36,ww-20,ParagraphStyle('cmp',parent=SMALL,fontSize=7.3,leading=9.7))
yy=sub(c,'Як перевірити зафіксовану швидкість',M,yy-176);yy=para(c,'Не змішуйте три рядки: спочатку знайдіть дозволений ліміт, потім виміряну швидкість, а далі швидкість після технічної поправки. Саме так видно, де закінчується правило знака й починається процедура фіксації. Якщо документ або ситуація незрозумілі, звіряйтеся з офіційним джерелом, а не з побутовим уявленням про «допуск».',M,yy,W-2*M,SMALL)
note(c,'ПРАКТИЧНИЙ ВИСНОВОК','У Франції плануйте швидкість від знака, загального правила та умов руху. Не використовуйте ані український поріг санкції, ані французьку поправку радара як спосіб додати швидкість.',M,yy-2,W-2*M,RED)
para(c,'Джерела: Code de la route R413-2; Sécurité routière, матеріали про радари; ПДР України, знак 3.29; КУпАП, ст. 122.',M,48,W-2*M,ParagraphStyle('src7',parent=SMALL,fontSize=6.5,leading=7.7,textColor=GRAY));foot(c,7,'Порівняння · швидкість');c.showPage()
# 8 review + index
y=page_head(c,'Повторення та пошук','Спочатку дія, потім термін','Ліва половина перевіряє впізнавання; права показує, як працюватиме двомовний покажчик.')
c.setFillColor(INK);c.setFont('Atlas-Bold',10.5);c.drawString(M,y,'Швидкий повтор')
review=[('AB4','повна зупинка'),('AB3a','дати дорогу'),('AB1','перевірити праворуч'),('AB25','поступитися на в’їзді'),('B14_30','точковий максимум'),('B52','зональний режим 20')]
for i,(code,ans) in enumerate(review):
 xx=M+(i%2)*124;yy=y-39-(i//2)*137;img(c,code,xx,yy-82,70);c.setFillColor(PALE);c.roundRect(xx,yy-100,102,18,4,fill=1,stroke=0);c.setFillColor(INK);c.setFont('Atlas',6.1);c.drawCentredString(xx+51,yy-94,ans)
x=M+CW+G;c.setFillColor(INK);c.setFont('Atlas-Bold',10.5);c.drawString(x,y,'Французький термін → українське поняття')
idx=[('arrêt','зупинка','AB4'),('cédez le passage','дати дорогу','AB3a'),('priorité à droite','пріоритет праворуч','AB1'),('sens giratoire','круговий рух','AB25'),('limitation de vitesse','обмеження швидкості','B14'),('zone de rencontre','зона зустрічі','B52')];yy=y-20
for fr,uk,code in idx:
 c.setFillColor(PALE);c.roundRect(x,yy-42,CW,35,4,fill=1,stroke=0);c.setFillColor(BLUE);c.setFont('Atlas-Bold',7.2);c.drawString(x+8,yy-21,fr);c.setFillColor(INK);c.setFont('Atlas',6.8);c.drawString(x+8,yy-33,uk);c.setFont('Atlas-Bold',6.8);c.drawRightString(x+CW-8,yy-26,code);yy-=46
note(c,'У ПОВНІЙ КНИЗІ','Коди, французькі терміни й українські поняття вестимуть на сторінки атласу; Kindle-версія матиме внутрішні посилання.',x,yy-3,CW,BLUE)
foot(c,8,'Швидкий повтор · покажчик');c.showPage();c.save()

r=PdfReader(str(OUT));text='\n'.join((pg.extract_text() or '') for pg in r.pages)
for forbidden in ('MATCH','NEAR_MATCH','DIFFERENT_SYSTEM','NO_DIRECT_ANALOGUE','Ви вже знаєте українську дорожню систему'):assert forbidden not in text,forbidden
qa={'schema_version':'rn3-091-v2-gate2-prototype-qa/v1','status':'PASS','pages':len(r.pages),'word_count':len(re.findall(r"\b[\wÀ-ÿА-Яа-яІіЇїЄє’'-]+\b",text)),'page_types':['prose_differences_1','prose_differences_2','dense_sign_primer','two_sign_atlas_1','two_sign_atlas_2','four_sign_atlas','important_comparison','quick_review_index'],'english_reader_taxonomy_absent':True,'global_prior_experience_assumption_absent':True,'full_production':'BLOCKED','human_product_gate':2,'human_gate_status':'PENDING','artifact':str(OUT.relative_to(ROOT))}
(V2/'qa/gate2-prototype-technical-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n');print(json.dumps(qa,ensure_ascii=False,indent=2))
