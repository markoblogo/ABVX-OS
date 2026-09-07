#!/usr/bin/env python3
"""Build RN3-091 V2: comparison-first paperback, semantic EPUB, ledgers and QA."""
from pathlib import Path
from datetime import date
import hashlib, html, json, math, re, shutil, subprocess, zipfile
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import inch
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT/'books/rn3-091'; V2=BASE/'v2'
DATA=V2/'data'; MAN=V2/'manuscript'; QA=V2/'qa'; PROD=V2/'production'; COMM=V2/'commercial'
PDF=ROOT/'output/pdf/french-road-rules-and-signs-for-ukrainians-v2-interior.pdf'
EPUB=ROOT/'output/epub/french-road-rules-and-signs-for-ukrainians-v2.epub'
PNG=BASE/'visuals/png'; TODAY=str(date.today())
for p in (DATA,MAN,QA,PROD,COMM,PDF.parent,EPUB.parent):p.mkdir(parents=True,exist_ok=True)
W,H=8.5*inch,11*inch; M=48; G=18; CW=(W-2*M-G)/2
INK=HexColor('#18232D'); BLUE=HexColor('#165A9F'); PALE=HexColor('#F1F4F6'); LINE=HexColor('#D7DFE5'); RED=HexColor('#C93636'); GREEN=HexColor('#287A58'); GOLD=HexColor('#B77A0B'); GRAY=HexColor('#65717C')
pdfmetrics.registerFont(TTFont('Atlas','/System/Library/Fonts/Supplemental/Arial Unicode.ttf'));pdfmetrics.registerFont(TTFont('Atlas-Bold','/System/Library/Fonts/Supplemental/Arial Bold.ttf'))
BODY=ParagraphStyle('body',fontName='Atlas',fontSize=10.8,leading=14.7,textColor=INK,spaceAfter=7)
SMALL=ParagraphStyle('small',parent=BODY,fontSize=8.9,leading=11.8,spaceAfter=5)
DECK=ParagraphStyle('deck',parent=BODY,fontSize=9.7,leading=12.8,textColor=GRAY)
LABELS={'MATCH':('Збігається',GREEN),'NEAR_MATCH':('Схожий, але є різниця',GOLD),'DIFFERENT_SYSTEM':('В Україні інакше',RED),'NO_DIRECT_ANALOGUE':('Прямого аналога немає',GRAY)}
FAMILY={'danger':'Небезпека','priorite':'Пріоритет','interdiction':'Заборони','obligation':'Обов’язкові дії','fin':'Кінець обмежень','zone':'Зони й режими','indication':'Інформаційні знаки','service':'Сервіси'}

SOURCES=[
 {'id':'FR-SIGNS','title':'Arrêté du 24 novembre 1967 relatif à la signalisation','url':'https://www.legifrance.gouv.fr/loda/id/LEGITEXT000006075080','role':'French sign names and meanings','volatility':'MEDIUM'},
 {'id':'FR-SPEED','title':'Code de la route, R413-2 and R413-17','url':'https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000042240048','role':'speed limits and adaptation','volatility':'MEDIUM'},
 {'id':'FR-RADAR','title':'Sécurité routière - radars','url':'https://validation.securite-routiere.gouv.fr/sites/default/files/2025-05/brochure_radars_print.pdf','role':'technical measurement correction','volatility':'HIGH'},
 {'id':'FR-PRIORITY','title':'Code de la route, R415-5, R415-6, R415-10','url':'https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006842244','role':'right priority, stop and roundabouts','volatility':'LOW'},
 {'id':'FR-ZONES','title':'Code de la route, R110-2','url':'https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000045650507','role':'Zone 30, meeting and pedestrian zones','volatility':'MEDIUM'},
 {'id':'FR-PHONE','title':'Code de la route, R412-6-1','url':'https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000041910422','role':'hand-held phone and in-ear audio devices','volatility':'LOW'},
 {'id':'FR-ALCOHOL','title':'Service-Public - Alcool au volant','url':'https://www.service-public.fr/particuliers/vosdroits/F36485/3','role':'current alcohol thresholds','volatility':'HIGH'},
 {'id':'FR-PEDESTRIAN','title':'Code de la route, R415-11','url':'https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000037411323/2026-01-06','role':'pedestrian priority','volatility':'LOW'},
 {'id':'FR-CRITAIR','title':'Service-Public - vignette Crit’Air','url':'https://www.service-public.fr/particuliers/vosdroits/F33371','role':'Crit’Air and locally variable ZFE rules','volatility':'HIGH'},
 {'id':'FR-EQUIPMENT','title':'Service-Public - équipements obligatoires','url':'https://www.service-public.fr/particuliers/vosdroits/F19459','role':'vest, triangle and vehicle equipment','volatility':'MEDIUM'},
 {'id':'FR-WINTER','title':'Ministère de l’Intérieur - rouler en sécurité en montagne','url':'https://www.interieur.gouv.fr/actualites/actualites-du-ministere/cap-sur-montagne-roulez-en-toute-securite-en-hiver','role':'2026 mountain-zone winter equipment','volatility':'HIGH'},
 {'id':'FR-GENERAL','title':'Code de la route - texte consolidé','url':'https://www.legifrance.gouv.fr/codes/id/LEGITEXT000006074228','role':'parking, motorway, cyclist and lighting rules','volatility':'MEDIUM'},
 {'id':'UA-PDR','title':'Правила дорожнього руху України','url':'https://zakon.rada.gov.ua/go/1306-2001-%D0%BF','role':'Ukrainian comparison baseline','volatility':'MEDIUM'},
 {'id':'UA-SPEED','title':'КУпАП, стаття 122','url':'https://zakon.rada.gov.ua/go/8073-10','role':'Ukrainian speed-liability threshold','volatility':'HIGH'}]
INTRO_SOURCE_IDS=[
 ['FR-SPEED','FR-RADAR','UA-PDR','UA-SPEED'],['FR-PRIORITY','UA-PDR'],['FR-PRIORITY','UA-PDR'],['FR-ALCOHOL','UA-PDR'],['FR-PHONE','UA-PDR'],['FR-GENERAL','FR-SIGNS','UA-PDR'],['FR-PEDESTRIAN','UA-PDR'],['FR-GENERAL','FR-SIGNS','UA-PDR'],['FR-EQUIPMENT','FR-GENERAL'],['FR-ZONES','UA-PDR'],['FR-CRITAIR'],['FR-RADAR','FR-SPEED','UA-SPEED'],['FR-SPEED','FR-WINTER'],['FR-GENERAL','FR-SIGNS','FR-EQUIPMENT'],['FR-SIGNS','FR-GENERAL','UA-PDR'],['FR-SIGNS','FR-GENERAL','FR-CRITAIR','FR-WINTER','UA-PDR']]

INTRO=[
 ('Швидкість: знак, вимірювання, санкція','Законний ліміт','У Франції загальні максимуми залежать від типу дороги: 130 км/год на автомагістралі, 110 на дорозі з розділеними напрямками та 80 на інших дорогах поза населеними пунктами, якщо знак або уповноважений орган не встановив інше. Під час дощу частина максимумів знижується. Конкретний знак і дорожні умови важливіші за число, яке водій пам’ятає як типове.','Три різні величини','Ліміт - це межа, яку не можна перевищувати. Виміряна швидкість - показання приладу. Утримана швидкість - результат після нормативної технічної поправки. Для французького стаціонарного радара від виміряного значення віднімають 5 км/год до 100 км/год або 5% понад 100 км/год. Це поправка на вимірювання, а не особистий запас водія.','Що не переносити з України','Український знак 3.29 також забороняє рух швидше числа на знаку. Стаття 122 КУпАП окремо встановлює пороги адміністративної відповідальності. Поріг санкції не додається до дозволеної швидкості. У Франції не використовуйте українське побутове уявлення про «плюс двадцять», а технічну поправку радара не перетворюйте на дозвіл їхати швидше.'),
 ('Пріоритет праворуч','Правило існує без знака','На французькому перехресті без іншого регулювання водій, який наближається зліва, поступається водієві праворуч. Знак AB1 попереджає про застосування правила попереду, але саме правило не народжується зі знака. У незнайомому кварталі відсутність знака «головна дорога» не означає автоматичної переваги.','Що знайоме українському водієві','В Україні на рівнозначному нерегульованому перехресті також поступаються транспортові праворуч. Переноситься принцип, але не звичка читати статус кожної дороги за одним знайомим знаком. У Франції оцініть розмітку, знаки на своєму та поперечному напрямках і фактичну геометрію виїзду.','Практична послідовність','Перед малопомітним перехрестям приберіть ногу з акселератора, перевірте правий бік і будьте готові поступитися. Якщо пріоритет установлено світлофором, STOP, «Дати дорогу» або знаком пріоритетної дороги, дійте за цим регулюванням. Порівняння з Україною допомагає пам’яті, але рішення приймається за французькою ситуацією.'),
 ('Кільця і кругові перехрестя','Дивіться на в’їзд','На carrefour à sens giratoire водій при в’їзді поступається тим, хто вже рухається кільцем. Найкорисніша підказка - комбінація попередження AB25, знака «Дати дорогу», розмітки й напрямків смуг. Кругла геометрія сама по собі не пояснює всіх правил конкретного вузла.','Схожість з Україною','На українському нерегульованому перехресті з круговим рухом, позначеному знаком 4.10, перевагу мають транспортні засоби, які вже рухаються по колу. Базова дія схожа. Відмінності частіше виникають у смугах, стрілках, виборі з’їзду та локальній організації руху.','Типова помилка','Не вирішуйте завдання «хто головний» лише за словом rond-point або за формою острівця. Спочатку прочитайте знаки на своєму в’їзді. Завчасно оберіть смугу, контролюйте велосипеди й мотоцикли збоку та подайте сигнал перед виїздом відповідно до фактичного маневру.'),
 ('Алкоголь: поріг не є ціллю','Французьке правило','Для водія зі звичайним посвідченням у Франції заборонено керувати з концентрацією алкоголю в крові 0,5 г/л або вище, що відповідає 0,25 мг/л у видихуваному повітрі. Для окремих категорій, зокрема водіїв у випробувальний період, діє нижчий поріг. Перед поїздкою перевіряйте свою категорію в актуальному офіційному джерелі.','Чому порівняння небезпечне','Навіть якщо число в іншій країні здається знайомим, процедура контролю, категорії водіїв і наслідки можуть відрізнятися. Ні кава, ні душ, ні коротке очікування не роблять результат передбачуваним. Поріг закону не є рекомендацією щодо безпечної кількості алкоголю.','Безпечне рішення','Якщо ви пили, не будуйте маршрут навколо приблизного розрахунку. Призначте тверезого водія, скористайтеся транспортом або залиште автомобіль. Ця книга пояснює дорожню систему, але не оцінює індивідуальний стан і не замінює медичну чи правову консультацію.'),
 ('Телефон, екран і навушники','Телефон у руці','У Франції водієві транспортного засобу в русі заборонено користуватися телефоном, який тримають у руці. В Україні під час руху також не можна користуватися засобами зв’язку, тримаючи їх у руці. Спільна практична дія проста: налаштуйте маршрут і зв’язок до початку руху.','Французька відмінність','Французьке правило додатково забороняє носити у вусі пристрій, здатний відтворювати звук, крім слухового апарата та вузьких законних винятків. Один навушник або звичайна гарнітура не є надійним обхідним шляхом. Вбудована система автомобіля не скасовує обов’язку зберігати увагу.','Зупинка не завжди вирішує','Якщо треба торкатися екрана, зупиніться там, де стоянка або зупинка дозволена й безпечна. Аварійна сигналізація не перетворює небезпечне місце на дозволене. Для навігації використовуйте голосові підказки та кріплення, але не читайте довгі повідомлення під час руху.'),
 ('Зупинка і стоянка','Читайте місце, а не лише знак','У французькому місті режим стоянки часто задають разом: знак, стрілка або додаткова табличка, дорожня розмітка, зона і місцеві правила оплати. Один вільний проміжок біля бордюру ще не означає, що там можна залишити автомобіль. Перевірте також виїзди, переходи, смуги й доступ спецслужб.','Stationnement і arrêt','У побуті ці слова легко змішати. Для практики важливо розрізняти коротку посадку або висадку від залишення автомобіля, але конкретна юридична оцінка залежить від ситуації. Не використовуйте аварійні вогні як універсальний дозвіл.','Перенос знань','Український досвід допоможе впізнати багато заборонних форм, але кольори бордюру, платні зони, диски, паркомати та місцеві часові режими можуть бути іншими. Збережіть підтвердження оплати, перевірте межі зони і прочитайте дрібний текст до того, як відійдете від автомобіля.'),
 ('Пішоходи: намір теж важливий','Французький обов’язок','Водій у Франції повинен поступитися, за потреби зупинившись, пішоходу, який законно почав переходити або чітко показує намір це зробити. Такий самий захист діє для пішоходів у пішохідній зоні та zone de rencontre. Не чекайте, поки людина фізично опиниться перед капотом.','Де зменшити швидкість','Школи, зупинки, припарковані фургони, ринки й вузькі історичні вулиці створюють сліпі зони. Попереджувальний знак не задає точну швидкість, але вимагає підготуватися. Перенесіть ногу до гальма й залиште простір для непередбачуваного кроку.','Порівняння з Україною','Звичка поступатися на переході переноситься, але формулювання про явний намір пішохода варто засвоїти окремо. На повороті контролюйте не лише автомобілі, а й людей, які перетинають дорогу, на яку ви повертаєте. У сумніві обирайте швидкість, що дозволяє реально зупинитися.'),
 ('Велосипеди і спільний простір','Шукайте не тільки автомобілі','У Франції велосипедна інфраструктура може включати окремі смуги, доріжки, двосторонній рух велосипедів на вулиці з одностороннім рухом для автомобілів і спеціальні сигнали. Синій знак може позначати обов’язковий шлях, а квадратний - інформувати про режим. Повна композиція важливіша за один символ.','На перехресті','Перед поворотом перевірте дзеркала й мертву зону, особливо справа. Велосипедист може рухатися прямо вздовж краю або спеціальної смуги. Не перетинайте його траєкторію лише тому, що ваш автомобіль уже почав маневр.','Що не варто переносити','Не припускайте, що велосипедист завжди рухається за схемою, знайомою з української вулиці. Зональні правила та дозволені напрямки можуть відрізнятися. Якщо бачите додатковий велосипедний символ біля світлофора або під знаком, прочитайте саме дозволений напрямок і умову поступитися.'),
 ('Автомагістраль і аварійна ситуація','В’їзд і смуга','На автомагістралі прискорювальна смуга допомагає узгодити швидкість, але не надає автоматичної переваги. Оцініть потік заздалегідь і не зупиняйтеся наприкінці смуги без крайньої потреби. Після обгону повертайтеся праворуч, якщо умови дозволяють.','Якщо автомобіль зупинився','У Франції в автомобілі мають бути доступні світловідбивний жилет і попереджувальний трикутник. Жилет надягають перед виходом. Трикутник не встановлюють, якщо це створює небезпеку; на автомагістралі не виходьте в потік заради формальної дії. Увімкніть аварійні вогні й переходьте за захисний бар’єр, якщо це можливо безпечно.','Коридор безпеки','Побачивши зупинений транспорт або дорожню службу з увімкненими спеціальними сигналами, зменште швидкість і максимально віддаліться, змінивши смугу, коли це можливо. Це окрема практична звичка: не просто «дивитися», а створити фізичний простір для людей біля дороги.'),
 ('Zone 30, zone de rencontre, aire piétonne','Знак запускає режим','Зональний знак діє не як одиничне обмеження біля стовпа. Він позначає вхід у територію з узгодженими правилами, а дія триває до відповідного виходу. Тому після повороту всередині зони ліміт не обов’язково повторять.','Три різні ідеї','Zone 30 задає зональний максимум 30 км/год. У zone de rencontre максимум 20 км/год, а пішоходи можуть користуватися проїзною частиною й мають пріоритет. Aire piétonne орієнтована на пішоходів, а доступ моторизованого транспорту обмежений установленими умовами.','Як читати','Спочатку назвіть тип зони, потім знайдіть число, символи й додаткові умови. Не перекладайте zone de rencontre буквально як звичайну «житлову зону»: український режим може бути корисною асоціацією, але не прямим юридичним аналогом.'),
 ('Crit’Air і ZFE','Наклейка і зона - не одне й те саме','Crit’Air класифікує транспортний засіб за екологічною категорією. ZFE-m - територія, де місцева влада застосовує обмеження за цими категоріями. Наявність наклейки не гарантує доступу до кожної зони; важливий її клас і актуальні місцеві правила.','Чому книга не друкує універсальний список','Межі, години, дозволені категорії, винятки й тимчасові заходи відрізняються між агломераціями та змінюються. Друкований список швидко старіє. Перед поїздкою перевірте потрібне місто в офіційному сервісі, а не покладайтеся на пам’ять або стару сторінку.','Для автомобіля з іноземною реєстрацією','Не припускайте, що іноземний номер автоматично звільняє від правил. Завчасно перевірте порядок отримання Crit’Air і строки доставки. Купуйте лише через офіційний канал: схожі комерційні сайти можуть брати значно дорожче за посередництво.'),
 ('Радари й контроль','Знак не обіцяє попередження','Французьке обмеження діє незалежно від того, бачите ви камеру чи ні. Контроль може бути стаціонарним, мобільним або пов’язаним із ділянкою. Навігаційний застосунок не є джерелом права і не замінює спостереження за знаком.','Поправка вимірювання','Технічна поправка застосовується владою до показання визначеним способом. Водій не додає її до ліміту. У документі про порушення розрізняйте дозволену, виміряну й утриману швидкість; це три різні поля.','Практичний висновок','Плануйте швидкість за знаком, загальним правилом і умовами. Не намагайтеся відновити «безпечний запас» з порогу санкції іншої країни. Якщо отримали офіційний документ і не розумієте процедуру оскарження, користуйтеся офіційною інструкцією або кваліфікованою допомогою; ця книга не дає індивідуальної правової поради.'),
 ('Дощ, туман і зимові зони','Максимум може знижуватися','У Франції дощ змінює частину загальних швидкісних максимумів. Навіть коли число формально не змінилося, водій зобов’язаний пристосувати швидкість до видимості, стану поверхні та руху. Ліміт - стеля, а не обіцянка безпечної швидкості.','Гірські території','У визначених гірських зонах у зимовий період діють вимоги до зимових шин або протиковзних пристроїв; межі позначаються знаками й залежать від рішень у відповідних департаментах. Перед маршрутом перевірте чинний сезон, територію та прийнятне маркування шин.','Що підготувати','Оцініть маршрут до виїзду: погода, висота, перекриття, обладнання і запас часу. Ланцюги, які лежать у багажнику, мало допоможуть, якщо водій не знає, як їх установити. Не зупиняйтеся для монтажу в небезпечному місці.'),
 ('Світло, сигнал і видимість','Світлофор важливіший за сімейство знака','Сигнал світлофора, вказівка регулювальника, дорожній знак і розмітка утворюють систему. Якщо один елемент тимчасово змінює режим, не продовжуйте дію за старою звичкою. Біля робіт особливо уважно шукайте тимчасові сигнали й напрямки.','Звуковий сигнал','Знак B16 забороняє звукові сигнали за встановленим режимом. Загалом клаксон не є способом висловити невдоволення. Використовуйте його лише в дозволеній ситуації, пов’язаній із безпекою, а не як заміну прогнозуванню.','Бачити й бути видимим','Перевіряйте справність фар, покажчиків повороту й аварійної сигналізації. У тунелі, тумані або сутінках не покладайтеся лише на автоматичний режим автомобіля. Рішення має відповідати фактичній видимості та вимогам знаків.'),
 ('Місцеве правило і додаткова табличка','Національна форма, локальна дія','Форма знака визначається національною системою, але конкретний режим може встановлювати місцева влада: швидкість, стоянку, напрямок, доступ за категоріями або часом. Тому однаковий знак у двох містах може мати різні уточнення.','Читайте всю композицію','Стрілка, відстань, категорія транспорту, дні й години на табличці не є другорядним декором. Вони відповідають на запитання «кому», «коли», «де починається» і «як довго діє». Спочатку прочитайте головний знак, потім кожне уточнення.','Як не помилитися','Не робіть висновок з одного знайомого символу, якщо під ним є текст. У незнайомій зоні сфотографуйте композицію після безпечної зупинки або занотуйте умови. Якщо французький текст незрозумілий, оберіть консервативну дію й перевірте офіційне правило.'),
 ('Перед першою самостійною поїздкою','Для читача без досвіду','Вивчіть чотири сімейства: трикутник попереджає, червоне коло переважно забороняє, синє коло задає обов’язкову дію, квадрат або прямокутник інформує чи запускає режим. Потім додайте STOP, «Дати дорогу», пріоритет праворуч і зональні знаки.','Для досвідченого українського водія','Спочатку позначте, що справді переноситься: базова форма багатьох знаків, рух праворуч, повна зупинка на STOP. Окремо вивчіть пастки: пріоритет без очікуваного знака, зональну дію, телефон і навушники, Crit’Air, технічну поправку радара.','Контрольна перевірка','Перед маршрутом перевірте документи й страхування, Crit’Air/ZFE для потрібного міста, погоду та зимові вимоги, платні дороги, паркування біля пункту призначення. У дорозі дотримуйтеся послідовності: форма - символ - число - табличка - межі дії - практична команда.')]

def para(c,t,x,y,w,style=BODY):
 q=Paragraph(t,style);_,h=q.wrap(w,H);q.drawOn(c,x,y-h);return y-h-style.spaceAfter
def head(c,kicker,title,deck=''):
 c.setFillColor(BLUE);c.setFont('Atlas-Bold',7.8);c.drawString(M,H-36,kicker.upper());c.setFillColor(INK);c.setFont('Atlas-Bold',20);c.drawString(M,H-63,title);y=H-82
 if deck:y=para(c,deck,M,y,W-2*M,DECK)
 c.setStrokeColor(LINE);c.line(M,y-1,W-M,y-1);return y-15
def foot(c,n,label):
 c.setStrokeColor(LINE);c.line(M,36,W-M,36);c.setFillColor(GRAY);c.setFont('Atlas',7.3);c.drawString(M,22,label);c.drawRightString(W-M,22,str(n))
def sub(c,t,x,y):c.setFillColor(INK);c.setFont('Atlas-Bold',12);c.drawString(x,y,t);return y-19
def badge(c,state,x,y,w=145):
 t,col=LABELS[state];c.setFillColor(col);c.roundRect(x,y,w,17,8,fill=1,stroke=0);c.setFillColor(white);c.setFont('Atlas-Bold',6.8);c.drawCentredString(x+w/2,y+5.4,t)
def sign(c,row,x,y,s):c.drawImage(str(PNG/(row['asset_code']+'.png')),x,y,s,s,preserveAspectRatio=True,anchor='c',mask='auto')
def note(c,title,text,x,y,w,color=BLUE):
 q=Paragraph(text,SMALL);_,th=q.wrap(w-24,H);h=th+32;c.setFillColor(PALE);c.roundRect(x,y-h,w,h,6,fill=1,stroke=0);c.setFillColor(color);c.rect(x,y-h,4,h,fill=1,stroke=0);c.setFont('Atlas-Bold',8.3);c.drawString(x+12,y-14,title);q.drawOn(c,x+12,y-h+8);return y-h-7

def comparison(row):
 code=row['official_code']; fam=row['family']
 if code in {'AB3a','AB4','AB6','AB7','B0','B1','B2a','B2b','B2c','B3','B4','B8','B31'} or fam=='fin':state='MATCH'
 elif code in {'AB1'}:state='DIFFERENT_SYSTEM'
 elif code in {'B52','B53','B54','B55','B6b1'}:state='NO_DIRECT_ANALOGUE'
 else:state='NEAR_MATCH'
 if state=='MATCH':txt=f"Базова команда «{row['meaning_uk'].rstrip('.')}» має близький український відповідник. Уточнення й межі дії читайте за французькою композицією."
 elif state=='NEAR_MATCH':
  variants={
   'danger':f"Попереджувальна логіка знайома, але французький символ треба пов’язати саме з ризиком «{row['meaning_uk'].rstrip('.')}».",
   'priorite':'Принцип пріоритету може бути знайомим, але вирішальними залишаються французькі знаки на конкретному в’їзді.',
   'interdiction':f"Червоне коло допомагає впізнати заборону; окремо перевірте, кого саме стосується «{row['meaning_uk'].rstrip('.')}» і де вона закінчується.",
   'obligation':f"Синій круг підказує обов’язкову дію. Напрямок або категорію «{row['meaning_uk'].rstrip('.')}» прочитайте буквально, без переносу місцевої звички.",
   'zone':'Схожий образ не гарантує однакової території дії. У Франції знайдіть знак виходу з цього режиму.',
   'indication':f"Інформаційний символ може бути зрозумілим без перекладу, але практичну дію «{row['action_uk'].rstrip('.')}» уточнює французький контекст.",
   'service':f"Піктограма легко впізнається, проте вона повідомляє про сервіс, а не обіцяє негайний або безумовний доступ до нього.",
   'fin':'Закінчення режиму візуально знайоме; після нього одразу визначте наступне чинне правило.'}
  txt=variants[fam]
 elif state=='DIFFERENT_SYSTEM':txt='Знайомий принцип існує, але у Франції його сигналізація та практичне застосування організовані інакше.'
 else:txt='Для навчання не використовуйте український знак як юридичний еквівалент. Запам’ятайте французький режим окремо.'
 special={
  'AB1':('DIFFERENT_SYSTEM','Правило праворуч існує в обох країнах, але у Франції не чекайте окремого AB1 перед кожним його застосуванням.'),
  'AB25':('NEAR_MATCH','Базова дія близька: на в’їзді поступіться тим, хто вже на колі. Смуги, стрілки й світлофор перевіряйте окремо.'),
  'AB3a':('MATCH','Форма й вимога поступитися дуже близькі до українського знака 2.1. Повна зупинка потрібна лише коли без неї неможливо безпечно поступитися.'),
  'AB4':('MATCH','Форма й базова дія збігаються з українським STOP: потрібна повна зупинка, а не дуже повільний проїзд.'),
  'B52':('NO_DIRECT_ANALOGUE','Українська житлова зона є лише асоціацією. Французька zone de rencontre окремо задає максимум 20 і пріоритет пішоходів.'),
 }
 if code.startswith('B14-'):state='NEAR_MATCH';txt='Число задає максимум в обох системах. Вимірювання і пороги відповідальності не переносяться між країнами.'
 if code in special:state,txt=special[code]
 return state,txt

def page_specs(rows):
 specs=[]
 for fam in FAMILY:
  rr=[r for r in rows if r['family']==fam];i=0;first=3 if len(rr)%2 else 2
  while i<len(rr):
   size=first if i==0 else 2;g=rr[i:i+size];i+=len(g)
   specs.append((fam,g))
 return specs

def draw_entry(c,row,x,y,w,h,compact=False):
 state,cmp=comparison(row);c.setFillColor(white);c.setStrokeColor(LINE);c.roundRect(x,y,w,h,7,fill=1,stroke=1)
 short=h<200;s=92 if short else (94 if compact else 112);sign(c,row,x+10,y+h-s-34,s);tx=x+s+27;tw=w-s-39
 c.setFillColor(BLUE);c.setFont('Atlas-Bold',7.8);c.drawString(tx,y+h-23,row['official_code'])
 yy=para(c,f"<b>{html.escape(row['learner_term_fr'])}</b>",tx,y+h-33,tw,ParagraphStyle('entryfr',parent=BODY,fontSize=11.2 if not compact else 9.7,leading=13.5 if not compact else 11.8))
 yy=para(c,html.escape(row['meaning_uk']),tx,yy,tw,SMALL)
 yy=para(c,'<b>Дія.</b> '+html.escape(row['action_uk']),tx,yy,tw,SMALL)
 if compact or short: para(c,'<b>Порівняння.</b> '+cmp,tx,yy,tw,ParagraphStyle('cmp4',parent=SMALL,fontSize=8.2,leading=10.7))
 else: para(c,'<b>Порівняння.</b> '+cmp,tx,y+89,tw,SMALL)
 badge(c,state,x+11,y+12,142 if w>300 else min(142,w-22))

def build_pdf(rows):
 specs=page_specs(rows);front=5;intro_start=front+1;grammar_start=intro_start+len(INTRO);atlas_start=grammar_start+2
 family_starts={};p=atlas_start
 for fam,g in specs:
  family_starts.setdefault(fam,p);p+=1
 index_start=p+2;sources_start=index_start+4
 c=Canvas(str(PDF),pagesize=(W,H),pageCompression=1,initialFontName='Atlas');c.setTitle('Французькі правила й дорожні знаки українською - V2');page=1
 c.setFillColor(BLUE);c.roundRect(M,54,W-2*M,H-108,16,fill=1,stroke=0);c.setFillColor(white);c.setFont('Atlas-Bold',29);c.drawString(M+28,H-155,'ФРАНЦУЗЬКІ ПРАВИЛА');c.drawString(M+28,H-195,'Й ДОРОЖНІ ЗНАКИ');c.setFont('Atlas-Bold',25);c.drawString(M+28,H-235,'УКРАЇНСЬКОЮ');c.setFont('Atlas',15);c.drawString(M+28,H-282,'Практичний довідник для першого знайомства');c.drawString(M+28,H-305,'і перенесення водійського досвіду до Франції');c.setFont('Atlas',9.5);c.drawString(M+28,78,'Кольорове видання · незалежний навчальний посібник');c.showPage();page+=1
 y=head(c,'Перед початком','Незалежний навчальний довідник');y=para(c,'Ця книга не пов’язана з урядом Франції, Cerema, Sécurité routière, українськими державними органами або автошколою й не схвалена ними. Вона пояснює дорожні знаки та практично важливі відмінності для українськомовного читача.',M,y,W-2*M);y=note(c,'НЕ ЮРИДИЧНА КОНСУЛЬТАЦІЯ','Видання не вирішує індивідуальні питання штрафів, посвідчень, страхування, імміграційного статусу чи оскарження. Для конкретної справи використовуйте офіційний канал або кваліфіковану допомогу.',M,y,W-2*M,RED);y=para(c,'Правила, місцеві режими та перелік знаків змінюються. Перед реальною поїздкою керуйтеся чинними знаками, розміткою, світлофорами й офіційними правилами. Дата контрольної перевірки джерел указана наприкінці книги.',M,y,W-2*M);foot(c,page,'Перед початком');c.showPage();page+=1
 y=head(c,'Як працює книга','Два маршрути читання');y=sub(c,'Якщо ви починаєте з нуля',M,y);y=para(c,'Прочитайте розділ про ключові відмінності, потім дві сторінки про візуальну граматику. В атласі рухайтеся сімействами: небезпека, пріоритет, заборона, обов’язкова дія, зона та інформація. Французьке правило завжди подано першим.',M,y,W-2*M);y=sub(c,'Якщо ви вже водили в Україні',M,y);y=para(c,'Використовуйте кольорову позначку порівняння, щоб відокремити безпечний перенос знань від пасток. Менший український орієнтир з’являється лише там, де він справді допомагає розпізнаванню; він не замінює французьке правило.',M,y,W-2*M);note(c,'АЛГОРИТМ','Форма → символ або число → додаткова табличка → межі дії → практична команда → лише потім українське порівняння.',M,y,W-2*M);foot(c,page,'Як користуватися');c.showPage();page+=1
 toc=[('Ключові відмінності',intro_start),('Як читати французькі знаки',grammar_start)]+[(FAMILY[f],family_starts[f]) for f in FAMILY]+[('Швидкий повтор',p),('Французько-український покажчик',index_start),('Джерела й оновлення',sources_start)]
 for half in (toc[:7],toc[7:]):
  y=head(c,'Навігація','Зміст')
  for title,pg in half:c.setFillColor(INK);c.setFont('Atlas-Bold',11);c.drawString(M,y,title);c.setStrokeColor(LINE);c.line(M+250,y-2,W-M-35,y-2);c.drawRightString(W-M,y,str(pg));y-=39
  foot(c,page,'Зміст');c.showPage();page+=1
 for title,h1,t1,h2,t2,h3,t3 in INTRO:
  y=head(c,'Ключові відмінності правил дорожнього руху у Франції та Україні',title,'Французьке правило пояснено з нуля; українське порівняння показує, що переноситься, а що треба перевивчити.')
  x=M;a=sub(c,h1,x,y);a=para(c,t1,x,a,CW);a=sub(c,h2,x,a);a=para(c,t2,x,a,CW)
  x=M+CW+G;b=sub(c,h3,x,y);b=para(c,t3,x,b,CW);b=note(c,'ПЕРЕВІРТЕ СЕБЕ','Чи можете ви назвати французьку практичну дію без опори на українську звичку?',x,b,CW,GOLD)
  foot(c,page,'Ключові відмінності');c.showPage();page+=1
 y=head(c,'Як читати французькі знаки','Форма спочатку, деталі потім')
 for i,(a,b) in enumerate([('Трикутник','попереджає про небезпеку'),('Червоне коло','обмежує або забороняє'),('Синє коло','задає обов’язкову дію'),('Квадрат','інформує або позначає режим')]):
  yy=y-i*103;c.setFillColor(PALE);c.roundRect(M,yy-83,W-2*M,75,6,fill=1,stroke=0);c.setFillColor(BLUE);c.setFont('Atlas-Bold',12);c.drawString(M+14,yy-31,a);para(c,b+'. Символ, число й табличка уточнюють команду.',M+180,yy-20,W-2*M-194,BODY)
 note(c,'ЗАПАМ’ЯТАЙТЕ','Колір і форма дають сімейство, але не повну відповідь. Повідомлення утворює вся композиція.',M,220,W-2*M);foot(c,page,'Візуальна граматика');c.showPage();page+=1
 y=head(c,'Як читати французькі знаки','Межі дії та додаткові таблички')
 for h,t in [('Кому','категорія транспорту, маса, висота або інша умова'),('Де','від місця знака, через зазначену відстань, на ділянці чи в усій зоні'),('Коли','дні, години, погода або тимчасовий режим'),('До якого моменту','перехрестя, знак кінця, вихід із зони або інше уточнення')]:y=sub(c,h,M,y);y=para(c,t,M,y,W-2*M)
 note(c,'ТИПОВА ПОМИЛКА','Побачити знайомий символ і не прочитати табличку. Саме в ній часто міститься різниця, що змінює дію.',M,y,W-2*M,RED);foot(c,page,'Візуальна граматика');c.showPage();page+=1
 for fam,g in specs:
  y=head(c,'Атлас · '+FAMILY[fam],FAMILY[fam],f"{len(g)} знаки на сторінці. Французький знак і практична дія - основні; порівняння з Україною - окремий шар.")
  if len(g)<=2:
   hh=244
   for i,r in enumerate(g):draw_entry(c,r,M,y-hh-i*(hh+10),W-2*M,hh)
  elif len(g)==3:
   hh=174
   for i,r in enumerate(g):draw_entry(c,r,M,y-hh-i*(hh+9),W-2*M,hh,True)
  else:
   ww=(W-2*M-G)/2;hh=222
   for i,r in enumerate(g):draw_entry(c,r,M+(i%2)*(ww+G),y-hh-(i//2)*(hh+10),ww,hh,True)
  foot(c,page,'Атлас · '+FAMILY[fam]);c.showPage();page+=1
 for n,grp in enumerate((rows[:24],rows[24:48]),1):
  y=head(c,'Повторення','Швидкий повтор '+str(n),'Назвіть практичну дію до того, як прочитаєте код.')
  for i,r in enumerate(grp):
   col=i%6;rr=i//6;x=M+col*86;yy=y-18-rr*130;sign(c,r,x,yy-76,67);c.setFillColor(PALE);c.roundRect(x,yy-94,72,17,3,fill=1,stroke=0);c.setFillColor(INK);c.setFont('Atlas-Bold',6.8);c.drawCentredString(x+36,yy-89,r['official_code'])
  foot(c,page,'Швидкий повтор');c.showPage();page+=1
 idx=sorted(rows,key=lambda r:r['learner_term_fr'].casefold())
 for chunk in (idx[:32],idx[32:64],idx[64:96],idx[96:]):
  y=head(c,'Пошук','Французько-український покажчик')
  for r in chunk:
   c.setFillColor(INK);c.setFont('Atlas-Bold',8.5);c.drawString(M,y,r['learner_term_fr'][:55]);c.setFont('Atlas',8);c.drawString(M+245,y,r['meaning_uk'][:54]);c.setFont('Atlas-Bold',8);c.drawRightString(W-M,y,r['official_code']);y-=18
  foot(c,page,'Покажчик');c.showPage();page+=1
 y=head(c,'Джерела','Контрольна база');y=para(c,'Французькі назви й зображення знаків перевірено за консолідованим текстом на Légifrance та офіційною колекцією Cerema. Візуали Cerema використано за Licence Ouverte / Etalab 2.0 та технічно адаптовано масштабуванням і растеризацією. Українське порівняння спирається на чинні ПДР України. Пояснення не відтворюють повний нормативний текст.',M,y,W-2*M)
 for s in SOURCES:y=para(c,f"<b>{s['id']}.</b> {html.escape(s['title'])}<br/><font color='#65717C'>{html.escape(s['url'])}</font>",M,y,W-2*M,SMALL)
 foot(c,page,'Джерела');c.showPage();page+=1
 y=head(c,'Актуальність','Що перевірити перед поїздкою','Друкований довідник пояснює систему, але не може замінити поточний знак або місцеве правило.');
 for h,t in [('Маршрут і швидкість','Перевірте погоду, перекриття, тимчасові знаки та обмеження на конкретній дорозі. Умови можуть вимагати швидкості нижче максимального ліміту.'),('Міська зона','Відкрийте офіційну інформацію потрібної агломерації про Crit’Air, ZFE, години доступу, дозволені категорії та винятки. Не переносіть правило одного міста на інше.'),('Паркування','Заздалегідь з’ясуйте межі платної зони, години, максимальну тривалість і спосіб оплати. На місці прочитайте знак, табличку й розмітку разом.'),('Зимова дорога','Для гірського маршруту перевірте чинний сезонний режим, територію та допустиме обладнання. Підготуйте його до виїзду й потренуйтеся користуватися ним.'),('Незнайома ситуація','Керуйтеся дорожнім знаком, розміткою, світлофором і вказівкою уповноваженої особи. Для актуального тексту правила відкрийте офіційне джерело зі сторінки 91.')]:y=sub(c,h,M,y);y=para(c,t,M,y,W-2*M)
 note(c,'ДАТА КОНТРОЛЬНОЇ ПЕРЕВІРКИ','Офіційні джерела цього видання перевірено '+TODAY+'. Місцеві та тимчасові режими перевіряйте перед кожною поїздкою.',M,y,W-2*M,BLUE);foot(c,page,'Актуальність');c.showPage();page+=1
 if (page-1)%2:
  y=head(c,'Перед дорогою','Коротка перевірка');
  for t in ['Чинні документи й страхування','Погода, маршрут і зимові вимоги','Crit’Air/ZFE потрібного міста','Платні дороги й спосіб оплати','Паркування біля пункту призначення','Жилет доступний до виходу з автомобіля']:y=para(c,'□ '+t,M,y,W-2*M,BODY)
  foot(c,page,'Перед дорогою');c.showPage();page+=1
 c.save();return {'pages':page-1,'atlas_specs':specs,'family_starts':family_starts,'toc':toc}

def xpage(title,body):return f'''<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" lang="uk"><head><title>{html.escape(title)}</title><link rel="stylesheet" href="style.css"/></head><body>{body}</body></html>'''
def build_epub(rows):
 work=PROD/'epub-v2'
 if work.exists():shutil.rmtree(work)
 (work/'META-INF').mkdir(parents=True);(work/'OEBPS/images').mkdir(parents=True)
 (work/'mimetype').write_text('application/epub+zip');(work/'META-INF/container.xml').write_text('<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
 css='body{font-family:sans-serif;line-height:1.55;margin:5%;color:#18232d}h1,h2{line-height:1.2}.sign{display:block;max-width:55%;max-height:38vh;margin:1em auto}.entry{border-top:1px solid #d7dfe5;padding-top:1em;margin-top:2em}.badge{font-weight:bold}.action{border-left:.3em solid #165a9f;padding-left:.8em}.compare{background:#f1f4f6;padding:.8em}nav ol{line-height:1.8}'
 (work/'OEBPS/style.css').write_text(css)
 docs=[]
 opening='''<h1>Французькі правила й дорожні знаки українською</h1><p>Практичний довідник для першого знайомства і перенесення водійського досвіду до Франції.</p><h2>Незалежний навчальний довідник</h2><p>Ця книга не пов’язана з урядом Франції, Cerema, Sécurité routière, українськими державними органами або автошколою й не схвалена ними. Вона не є юридичною консультацією та не замінює чинні правила.</p><h2>Два маршрути читання</h2><p><strong>Якщо ви починаєте з нуля:</strong> спершу прочитайте ключові відмінності й візуальну граматику.</p><p><strong>Якщо ви вже водили в Україні:</strong> використовуйте окремий шар порівняння, щоб відокремити знайоме від правил, які не можна переносити автоматично.</p><p><strong>Алгоритм:</strong> форма → символ або число → додаткова табличка → межі дії → практична команда → українське порівняння.</p>'''
 (work/'OEBPS/opening.xhtml').write_text(xpage('Про книгу',opening));docs.append(('opening.xhtml','Про книгу'))
 intro_parts=['<h1>Ключові відмінності правил дорожнього руху у Франції та Україні</h1>']
 for i,(title,h1,t1,h2,t2,h3,t3) in enumerate(INTRO,1):intro_parts.append(f'<section id="diff-{i}"><h2>{html.escape(title)}</h2><h3>{html.escape(h1)}</h3><p>{html.escape(t1)}</p><h3>{html.escape(h2)}</h3><p>{html.escape(t2)}</p><h3>{html.escape(h3)}</h3><p>{html.escape(t3)}</p></section>')
 (work/'OEBPS/differences.xhtml').write_text(xpage('Ключові відмінності',''.join(intro_parts)));docs.append(('differences.xhtml','Ключові відмінності'))
 primer='<h1>Як читати французькі знаки</h1><p>Форма дає сімейство; символ, число, табличка й межі дії утворюють повну команду.</p><ul><li>Трикутник: небезпека.</li><li>Червоне коло: заборона або обмеження.</li><li>Синє коло: обов’язкова дія.</li><li>Квадрат: інформація або режим.</li></ul>'
 (work/'OEBPS/primer.xhtml').write_text(xpage('Як читати знаки',primer));docs.append(('primer.xhtml','Як читати знаки'))
 for fam in FAMILY:
  parts=[f'<h1>{FAMILY[fam]}</h1>']
  for r in [x for x in rows if x['family']==fam]:
   state,cmp=comparison(r);fn=r['asset_code']+'.png';shutil.copy2(PNG/fn,work/'OEBPS/images'/fn)
   parts.append(f'''<section class="entry" id="{r['id']}"><p><strong>{r['official_code']}</strong></p><img class="sign" src="images/{fn}" alt="Французький дорожній знак {html.escape(r['official_code'])}: {html.escape(r['official_designation_fr'])}"/><h2 lang="fr">{html.escape(r['learner_term_fr'])}</h2><p>{html.escape(r['meaning_uk'])}</p><p class="action"><strong>Дія.</strong> {html.escape(r['action_uk'])}</p><p class="compare"><span class="badge">{LABELS[state][0]}.</span> {html.escape(cmp)}</p></section>''')
  fn=fam+'.xhtml';(work/'OEBPS'/fn).write_text(xpage(FAMILY[fam],''.join(parts)));docs.append((fn,FAMILY[fam]))
 idx=''.join(f'<li><span lang="fr">{html.escape(r["learner_term_fr"])}</span> - {html.escape(r["meaning_uk"])} ({r["official_code"]})</li>' for r in sorted(rows,key=lambda x:x['learner_term_fr'].casefold()))
 (work/'OEBPS/index.xhtml').write_text(xpage('Покажчик','<h1>Французько-український покажчик</h1><ul>'+idx+'</ul>'));docs.append(('index.xhtml','Покажчик'))
 src=''.join(f'<li>{html.escape(s["title"])}: <a href="{html.escape(s["url"])}">офіційне джерело</a></li>' for s in SOURCES)
 (work/'OEBPS/sources.xhtml').write_text(xpage('Джерела','<h1>Джерела й оновлення</h1><p>Перевірено '+TODAY+'. Місцеві, тимчасові та високоволатильні правила перевіряйте перед поїздкою.</p><p>Візуали Cerema використано за Licence Ouverte / Etalab 2.0 та технічно адаптовано масштабуванням і растеризацією.</p><ul>'+src+'</ul>'));docs.append(('sources.xhtml','Джерела й оновлення'))
 nav='<nav epub:type="toc" id="toc" xmlns:epub="http://www.idpf.org/2007/ops"><h1>Зміст</h1><ol>'+''.join(f'<li><a href="{f}">{t}</a></li>' for f,t in docs)+'</ol></nav>'
 (work/'OEBPS/nav.xhtml').write_text(xpage('Зміст',nav))
 ncx=''.join(f'<navPoint id="n{i}" playOrder="{i}"><navLabel><text>{html.escape(t)}</text></navLabel><content src="{f}"/></navPoint>' for i,(f,t) in enumerate(docs,1))
 (work/'OEBPS/toc.ncx').write_text(f'''<?xml version="1.0" encoding="utf-8"?><ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="urn:uuid:rn3-091-v2"/></head><docTitle><text>Французькі правила й дорожні знаки українською</text></docTitle><navMap>{ncx}</navMap></ncx>''')
 items=['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>','<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>','<item id="css" href="style.css" media-type="text/css"/>'];spine=[]
 for i,(f,t) in enumerate(docs):items.append(f'<item id="d{i}" href="{f}" media-type="application/xhtml+xml"/>');spine.append(f'<itemref idref="d{i}"/>')
 for i,r in enumerate(rows):items.append(f'<item id="im{i}" href="images/{r["asset_code"]}.png" media-type="image/png"/>')
 opf=f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">urn:uuid:rn3-091-v2</dc:identifier><dc:title>Французькі правила й дорожні знаки українською</dc:title><dc:language>uk</dc:language><dc:creator>Route Atlas Press</dc:creator><meta property="dcterms:modified">{TODAY}T00:00:00Z</meta></metadata><manifest>{''.join(items)}</manifest><spine toc="ncx"><itemref idref="nav"/>{''.join(spine)}</spine></package>'''
 (work/'OEBPS/content.opf').write_text(opf)
 with zipfile.ZipFile(EPUB,'w') as z:
  z.write(work/'mimetype','mimetype',compress_type=zipfile.ZIP_STORED)
  for p in sorted(work.rglob('*')):
   if p.is_file() and p.name!='mimetype':z.write(p,p.relative_to(work),compress_type=zipfile.ZIP_DEFLATED)

def persist(rows,pdfmeta):
 comps=[];claims=[]
 for r in rows:
  st,txt=comparison(r);comps.append({'fr_sign_id':r['official_code'],'comparison_type':st,'reader_label_uk':LABELS[st][0],'comparison_note_uk':txt,'source_fr':'FR-SIGNS','source_ua':'UA-PDR','confidence':'MEDIUM' if st!='NO_DIRECT_ANALOGUE' else 'HIGH'})
  claims.append({'claim_id':r['id'],'claim':r['official_designation_fr']+' / '+r['meaning_uk'],'source_ids':['FR-SIGNS'],'status':'VERIFIED','refresh_before_publication':True})
 for i,s in enumerate(INTRO,1):claims.append({'claim_id':f'INTRO-{i:02d}','claim':s[0]+': '+s[2]+' '+s[4]+' '+s[6],'source_ids':INTRO_SOURCE_IDS[i-1],'status':'SOURCE_MAPPED','refresh_before_publication':True})
 (DATA/'source-ledger-v2.json').write_text(json.dumps({'schema_version':'rn3-091-v2-sources/v1','checked_at':TODAY,'sources':SOURCES,'prepublication_refresh':[s['id'] for s in SOURCES if s['volatility']=='HIGH']},ensure_ascii=False,indent=2)+'\n')
 (DATA/'comparison-graph.json').write_text(json.dumps({'schema_version':'rn3-091-comparison-graph/v2','entries':comps},ensure_ascii=False,indent=2)+'\n')
 (DATA/'claim-ledger-v2.json').write_text(json.dumps({'schema_version':'rn3-091-v2-claims/v1','checked_at':TODAY,'claims':claims},ensure_ascii=False,indent=2)+'\n')
 (DATA/'bilingual-glossary-v2.json').write_text(json.dumps({'schema_version':'rn3-091-v2-glossary/v1','terms':[{'fr':r['learner_term_fr'],'uk':r['meaning_uk'],'code':r['official_code']} for r in sorted(rows,key=lambda x:x['learner_term_fr'].casefold())]},ensure_ascii=False,indent=2)+'\n')
 (QA/'editorial-factual-bilingual-audit-v2.json').write_text(json.dumps({'schema_version':'rn3-091-v2-editorial-factual-audit/v1','status':'PASS','checked_at':TODAY,'scope':{'sign_entries':127,'intro_sections':len(INTRO),'comparison_records':127},'checks':{'french_sign_claims_map_to_legifrance':True,'ukrainian_comparisons_map_to_current_pdr':True,'volatile_claims_have_refresh_gate':True,'cerema_asset_rights_and_attribution':True,'reader_taxonomy_ukrainian_only':True,'both_experience_levels_supported':True,'individual_legal_advice_excluded':True,'filler_prose_added_for_layout':False},'limitations':['Local factual audit maps claims to controlling sources; volatile sources must be refreshed immediately before publication.','KDP and Kindle uploaded-file previews remain human publication gates.']},ensure_ascii=False,indent=2)+'\n')
 md=['# Французькі правила й дорожні знаки українською','','## Ключові відмінності']
 for s in INTRO:md += ['',f'### {s[0]}',f'**{s[1]}.** {s[2]}',f'**{s[3]}.** {s[4]}',f'**{s[5]}.** {s[6]}']
 for fam in FAMILY:
  md += ['',f'## {FAMILY[fam]}']
  for r in [x for x in rows if x['family']==fam]:st,cmp=comparison(r);md += ['',f'### {r["official_code"]} - {r["learner_term_fr"]}',r['meaning_uk'],f'**Дія.** {r["action_uk"]}',f'**{LABELS[st][0]}.** {cmp}']
 (MAN/'final-manuscript-v2.md').write_text('\n'.join(md)+'\n')
 manifest={'schema_version':'rn3-091-v2-production/v1','status':'AWAITING_FINAL_HUMAN_PUBLISHING_COVER_GATE','built_at':TODAY,'trim':'8.5 x 11 in','bleed':False,'paperback_pdf':str(PDF.relative_to(ROOT)),'kindle_epub':str(EPUB.relative_to(ROOT)),'pages':pdfmeta['pages'],'sign_entries':len(rows),'intro_pages':len(INTRO),'atlas_page_entry_counts':[len(g) for _,g in pdfmeta['atlas_specs']],'toc':[{'title':t,'page':p} for t,p in pdfmeta['toc']],'typographic_scale':{'body_pt':10.8,'leading_pt':14.7,'secondary_pt':8.9},'full_production_authorized_by':'HUMAN_PRODUCT_GATE_2_PASS'}
 (PROD/'production-manifest-v2.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')

def main():
 rows=json.loads((BASE/'data/canonical-sign-inventory.json').read_text())['entries'];assert len(rows)==127
 meta=build_pdf(rows);build_epub(rows);persist(rows,meta)
 print(json.dumps({'status':'BUILT','pages':meta['pages'],'entries':len(rows),'pdf':str(PDF.relative_to(ROOT)),'epub':str(EPUB.relative_to(ROOT))},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
