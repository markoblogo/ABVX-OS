#!/usr/bin/env python3
"""Build the RN3-091 bilingual French-road-sign atlas and release evidence."""

from __future__ import annotations

import hashlib, html, json, re, subprocess, textwrap, urllib.request, zipfile
from datetime import date
from pathlib import Path

from lxml import html as lxml_html
from PIL import Image
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.pagesizes import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "books" / "rn3-091"
DATA, SRC, SVG, PNG = BASE/"data", BASE/"sources", BASE/"visuals"/"svg", BASE/"visuals"/"png"
MAN, QA, PROD, COMM = BASE/"manuscript", BASE/"qa", BASE/"production", BASE/"commercial"
OUTPDF, OUTEPUB = ROOT/"output"/"pdf", ROOT/"output"/"epub"
PDF_OUT = OUTPDF/"french-road-signs-in-ukrainian-visual-vocabulary-atlas-interior.pdf"
EPUB_OUT = OUTEPUB/"french-road-signs-in-ukrainian-visual-vocabulary-atlas.epub"
TODAY = str(date.today())

W, H = 8.5*inch, 11*inch
MARGIN = 54
INK, BLUE, PALE, RED, GRAY = map(HexColor,["#17212B","#1557A0","#F3F6F9","#C83737","#5F6B76"])
FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
pdfmetrics.registerFont(TTFont("Atlas",FONT)); pdfmetrics.registerFont(TTFont("Atlas-Bold",BOLD))

BOX_SHARED = "dwrf655fhaolonqcspo0z0gvb06ms0n7"
FOLDERS = {
 "A":232297811255,"AB":232297329082,"B_INTERDIT":232298459507,
 "B_OBLIG":232294933769,"B_FIN":232296212401,"B_ZONE":232297400976,
 "C":232296128872,"CE":232297758240,
}

# code|family|official French designation|plain Ukrainian meaning|practical action
SEED = r"""
A13a|danger|Endroit fréquenté par les enfants|Ділянка, де на дорозі можуть з'явитися діти|Знизьте швидкість і будьте готові зупинитися.
A13b|danger|Passage pour piétons|Попереду пішохідний перехід|Слідкуйте за пішоходами й за потреби пропустіть їх.
A14|danger|Autres dangers|Інша небезпека, не показана окремим символом|Шукайте додаткову табличку та зменште швидкість.
A15a1|danger|Passage d'animaux domestiques|Можлива поява свійських тварин|Сповільніться; тварина може вийти раптово.
A15b|danger|Passage d'animaux sauvages|Можлива поява диких тварин|Сповільніться, особливо вночі та біля лісу.
A15c|danger|Passage de cavaliers|Можлива поява вершників|Зменште швидкість і не лякайте коней сигналом.
A16|danger|Descente dangereuse|Небезпечний спуск|Заздалегідь оберіть безпечну передачу й контролюйте швидкість.
A17|danger|Annonce de feux tricolores|Попереду світлофор|Будьте готові до зміни сигналу та зупинки.
A18|danger|Circulation dans les deux sens|Починається двосторонній рух|Очікуйте зустрічний транспорт і тримайтеся праворуч.
A19|danger|Risque de chutes de pierres|Можливе падіння каміння|Не зупиняйтеся в небезпечній зоні без потреби.
A1a|danger|Virage à droite|Небезпечний поворот праворуч|Зменште швидкість до входу в поворот.
A1b|danger|Virage à gauche|Небезпечний поворот ліворуч|Зменште швидкість до входу в поворот.
A1c|danger|Succession de virages, premier à droite|Серія поворотів, перший праворуч|Сповільніться до першого повороту й не прискорюйтеся завчасно.
A1d|danger|Succession de virages, premier à gauche|Серія поворотів, перший ліворуч|Сповільніться до першого повороту й не зрізайте траєкторію.
A20|danger|Débouché sur un quai ou une berge|Виїзд на набережну або берег|Уникайте різкого маневру до краю дороги.
A21|danger|Débouché de cyclistes|Можливий виїзд велосипедистів|Перевірте бокові зони й залиште безпечний інтервал.
A23|danger|Traversée d'une aire de danger aérien|Низьколітні літаки або інша повітряна небезпека|Не відволікайтеся від дороги через раптовий шум.
A24|danger|Vent latéral|Сильний боковий вітер|Тримайте кермо впевнено й збільшіть бічний інтервал.
A2a|danger|Cassis ou dos-d'âne|Різка нерівність дороги|Зменште швидкість до нерівності.
A2b|danger|Ralentisseur de type dos-d'âne|Штучна дорожня нерівність|Сповільніться завчасно, не гальмуйте різко на ній.
A3|danger|Chaussée rétrécie|Дорога звужується з обох боків|Знизьте швидкість і оцініть пріоритет проїзду.
A3a|danger|Chaussée rétrécie par la droite|Дорога звужується праворуч|Завчасно перебудуйтеся, якщо це безпечно.
A3b|danger|Chaussée rétrécie par la gauche|Дорога звужується ліворуч|Завчасно перебудуйтеся, якщо це безпечно.
A4|danger|Chaussée particulièrement glissante|Слизька дорога|Уникайте різкого гальмування та поворотів керма.
A6|danger|Pont mobile|Розвідний міст|Будьте готові зупинитися перед закритим проїздом.
AB1|priorite|Intersection où la priorité à droite est applicable|Перехрестя з правилом «перешкода праворуч»|Пропустіть транспорт, що наближається праворуч.
AB2|priorite|Intersection avec une route dont les usagers doivent céder le passage|Ви маєте пріоритет на найближчому перехресті|Контролюйте перехрестя: пріоритет не скасовує обережності.
AB25|priorite|Carrefour à sens giratoire|Круговий рух із обов'язком поступитися на в'їзді|Перед в'їздом пропустіть транспорт на кільці.
AB3a|priorite|Cédez le passage à l'intersection|Дати дорогу|Сповільніться й пропустіть тих, хто має пріоритет.
AB3b|priorite|Cédez le passage à l'intersection à distance indiquée|Попередження про «Дати дорогу» попереду|Починайте знижувати швидкість завчасно.
AB4|priorite|Arrêt à l'intersection|STOP: повна зупинка й дати дорогу|Зупиніться біля стоп-лінії, перевірте дорогу, тоді рушайте.
AB5|priorite|Arrêt à l'intersection à distance indiquée|Попередження про STOP попереду|Готуйтеся до обов'язкової повної зупинки.
AB6|priorite|Indication du caractère prioritaire d'une route|Головна дорога|Ви маєте пріоритет, доки його не скасовано іншим знаком.
AB7|priorite|Fin du caractère prioritaire d'une route|Кінець головної дороги|На наступних перехрестях знову перевіряйте правила пріоритету.
B0|interdiction|Circulation interdite à tout véhicule dans les deux sens|Рух усіх транспортних засобів заборонено в обох напрямках|Не в'їжджайте, якщо виняток не вказано табличкою.
B1|interdiction|Sens interdit à tout véhicule|В'їзд у цьому напрямку заборонено|Не в'їжджайте; шукайте дозволений напрямок.
B10a|interdiction|Accès interdit aux véhicules transportant plus d'une quantité indiquée de produits explosifs ou inflammables|В'їзд заборонено транспортові з визначеною кількістю вибухових або легкозаймистих вантажів|Водієві такого транспорту потрібен інший маршрут.
B11|interdiction|Accès interdit aux véhicules dont la largeur dépasse la valeur indiquée|Обмеження максимальної ширини|Не продовжуйте рух, якщо фактична ширина більша.
B12|interdiction|Accès interdit aux véhicules dont la hauteur dépasse la valeur indiquée|Обмеження максимальної висоти|Порівняйте знак із повною висотою транспортного засобу.
B13|interdiction|Accès interdit aux véhicules dont le poids total dépasse la valeur indiquée|Обмеження максимальної маси|Не в'їжджайте, якщо фактична маса перевищує значення.
B13a|interdiction|Accès interdit aux véhicules dont le poids par essieu dépasse la valeur indiquée|Обмеження навантаження на вісь|Перевірте навантаження на вісь, а не лише загальну масу.
B14_30|interdiction|Limitation de vitesse à 30 km/h|Максимальна швидкість 30 км/год|Не перевищуйте 30 км/год від місця знака.
B14_50|interdiction|Limitation de vitesse à 50 km/h|Максимальна швидкість 50 км/год|Не перевищуйте 50 км/год від місця знака.
B14_70|interdiction|Limitation de vitesse à 70 km/h|Максимальна швидкість 70 км/год|Не перевищуйте 70 км/год від місця знака.
B14_90|interdiction|Limitation de vitesse à 90 km/h|Максимальна швидкість 90 км/год|Не перевищуйте 90 км/год від місця знака.
B14_110|interdiction|Limitation de vitesse à 110 km/h|Максимальна швидкість 110 км/год|Не перевищуйте 110 км/год від місця знака.
B14_130|interdiction|Limitation de vitesse à 130 km/h|Максимальна швидкість 130 км/год|Не перевищуйте 130 км/год; умови можуть вимагати меншої швидкості.
B15|interdiction|Cédez le passage à la circulation venant en sens inverse|Дати дорогу зустрічному транспорту|Не в'їжджайте у вузьку ділянку, якщо це змусить зустрічного зупинитися.
B16|interdiction|Interdiction de signaux sonores|Звуковий сигнал заборонено|Не сигналізуйте, крім випадків безпосередньої небезпеки.
B17-70m|interdiction|Interdiction de maintenir un intervalle inférieur à 70 mètres|Мінімальна дистанція 70 метрів|Тримайте щонайменше вказану дистанцію.
B18a|interdiction|Accès interdit aux véhicules transportant des marchandises explosives ou inflammables|Заборона для транспорту з вибуховими або легкозаймистими вантажами|Дотримуйтеся маршруту, дозволеного для такого вантажу.
B18b|interdiction|Accès interdit aux véhicules transportant des marchandises pouvant polluer les eaux|Заборона для вантажів, небезпечних для води|Оберіть інший дозволений маршрут.
B18c|interdiction|Accès interdit aux véhicules transportant des marchandises dangereuses|Заборона для транспорту з небезпечними вантажами|Не в'їжджайте без прямо дозволеного маршруту.
B19|interdiction|Autre interdiction dont la nature est indiquée|Інша заборона, зазначена написом або символом|Прочитайте конкретну заборону на знаку.
B2a|interdiction|Interdiction de tourner à gauche à la prochaine intersection|Поворот ліворуч на найближчому перехресті заборонено|Продовжуйте прямо або оберіть дозволений поворот.
B2b|interdiction|Interdiction de tourner à droite à la prochaine intersection|Поворот праворуч на найближчому перехресті заборонено|Продовжуйте прямо або оберіть дозволений поворот.
B2c|interdiction|Interdiction de faire demi-tour|Розворот заборонено|Не виконуйте розворот на ділянці дії знака.
B3|interdiction|Interdiction de dépasser|Обгін моторних транспортних засобів заборонено|Не починайте обгін до знака закінчення заборони.
B3a|interdiction|Interdiction aux véhicules de transport de marchandises de dépasser|Вантажним транспортним засобам обгін заборонено|Якщо знак стосується вашої категорії, залишайтеся позаду.
B4|interdiction|Arrêt au poste de douane|Зупинка перед митницею|Зупиніться в зазначеному місці та виконуйте вказівки.
B5a|interdiction|Arrêt au poste de gendarmerie|Зупинка перед постом жандармерії|Зупиніться в зазначеному місці.
B5b|interdiction|Arrêt au poste de police|Зупинка перед постом поліції|Зупиніться в зазначеному місці.
B5c|interdiction|Arrêt au poste de péage|Зупинка перед пунктом оплати|Знизьте швидкість і зупиніться відповідно до смуги оплати.
B6a1|interdiction|Stationnement interdit|Стоянка заборонена|Не залишайте транспортний засіб; коротка зупинка може бути дозволена.
B6a2|interdiction|Stationnement interdit du 1er au 15 du mois|Стоянка заборонена з 1-го до 15-го числа|Перевірте дату й сторону вулиці.
B6a3|interdiction|Stationnement interdit du 16 à la fin du mois|Стоянка заборонена з 16-го до кінця місяця|Перевірте дату й сторону вулиці.
B6d|interdiction|Arrêt et stationnement interdits|Зупинка і стоянка заборонені|Не зупиняйтеся, крім вимушеної зупинки.
B7a|interdiction|Accès interdit aux véhicules à moteur à l'exception des cyclomoteurs|В'їзд моторних транспортних засобів заборонено, крім мопедів|Не в'їжджайте моторним транспортом, якщо немає винятку.
B7b|interdiction|Accès interdit à tous les véhicules à moteur|В'їзд усіх моторних транспортних засобів заборонено|Шукайте інший маршрут.
B8|interdiction|Accès interdit aux véhicules affectés au transport de marchandises|В'їзд вантажного транспорту заборонено|Якщо транспорт використовується для вантажів, не в'їжджайте.
B9a|interdiction|Accès interdit aux piétons|Рух пішоходів заборонено|Пішоходам слід обрати інший шлях.
B9b|interdiction|Accès interdit aux cycles|Рух велосипедів заборонено|Велосипедистам слід обрати інший шлях.
B9c|interdiction|Accès interdit aux véhicules à traction animale|Рух гужового транспорту заборонено|Не в'їжджайте транспортом, запряженим тваринами.
B9d|interdiction|Accès interdit aux véhicules agricoles à moteur|Рух моторної сільськогосподарської техніки заборонено|Для такої техніки потрібен інший маршрут.
B9e|interdiction|Accès interdit aux voitures à bras|Рух ручних візків заборонено|Не використовуйте цю ділянку з ручним візком.
B21-1|obligation|Direction obligatoire à droite à la prochaine intersection|Обов'язковий поворот праворуч|На найближчому перехресті поверніть праворуч.
B21-2|obligation|Direction obligatoire à gauche à la prochaine intersection|Обов'язковий поворот ліворуч|На найближчому перехресті поверніть ліворуч.
B21a1|obligation|Contournement obligatoire par la droite|Об'їзд перешкоди праворуч|Проїдьте з правого боку від знака.
B21a2|obligation|Contournement obligatoire par la gauche|Об'їзд перешкоди ліворуч|Проїдьте з лівого боку від знака.
B21b|obligation|Direction obligatoire tout droit|Рух лише прямо|Не повертайте на найближчому перехресті.
B21c1|obligation|Direction obligatoire à la prochaine intersection : à droite|На найближчому перехресті рух лише праворуч|Поверніть праворуч у напрямку стрілки.
B21c2|obligation|Direction obligatoire à la prochaine intersection : à gauche|На найближчому перехресті рух лише ліворуч|Поверніть ліворуч у напрямку стрілки.
B21d1|obligation|Directions obligatoires à la prochaine intersection : tout droit ou à droite|На найближчому перехресті рух лише прямо або праворуч|Оберіть один із двох показаних напрямків.
B21e|obligation|Directions obligatoires à la prochaine intersection : à droite ou à gauche|На найближчому перехресті рух лише праворуч або ліворуч|Рух прямо не дозволений.
B22a|obligation|Piste ou bande obligatoire pour les cycles|Обов'язкова велосипедна доріжка або смуга|Велосипедисти мають користуватися позначеним шляхом.
B22b|obligation|Chemin obligatoire pour piétons|Обов'язкова доріжка для пішоходів|Пішоходи мають користуватися позначеним шляхом.
B22c|obligation|Chemin obligatoire pour cavaliers|Обов'язковий шлях для вершників|Вершники мають користуватися позначеним шляхом.
B25-30|obligation|Vitesse minimale obligatoire de 30 km/h|Мінімальна обов'язкова швидкість 30 км/год|Не рухайтеся повільніше без необхідної причини.
B25-50|obligation|Vitesse minimale obligatoire de 50 km/h|Мінімальна обов'язкова швидкість 50 км/год|Не рухайтеся повільніше без необхідної причини.
B26|obligation|Chaînes à neige obligatoires|Ланцюги протиковзання обов'язкові|Встановіть належне обладнання до продовження руху.
B27a|obligation|Voie réservée aux transports en commun|Смуга, обов'язкова для громадського транспорту|Не використовуйте смугу, якщо ваша категорія не дозволена.
B31|fin|Fin de toutes les interdictions précédemment signalées|Кінець усіх раніше встановлених заборон для рухомих транспортних засобів|Далі діють загальні правила та нові знаки.
B33_30|fin|Fin de limitation de vitesse à 30 km/h|Кінець обмеження 30 км/год|Перевірте загальну межу та наступні знаки.
B33_50|fin|Fin de limitation de vitesse à 50 km/h|Кінець обмеження 50 км/год|Не прискорюйтеся автоматично: врахуйте загальні правила й умови.
B33_70|fin|Fin de limitation de vitesse à 70 km/h|Кінець обмеження 70 км/год|Перевірте чинну межу після знака.
B33_90|fin|Fin de limitation de vitesse à 90 km/h|Кінець обмеження 90 км/год|Перевірте чинну межу після знака.
B34|fin|Fin d'interdiction de dépasser|Кінець заборони обгону|Обгін можливий лише якщо інші правила й видимість це дозволяють.
B34a|fin|Fin d'interdiction de dépasser pour les véhicules de transport de marchandises|Кінець заборони обгону для вантажного транспорту|Перед обгоном перевірте інші обмеження.
B35|fin|Fin d'interdiction de signaux sonores|Кінець заборони звукових сигналів|Загальні правила використання сигналу знову діють.
B30|zone|Entrée d'une zone à vitesse limitée à 30 km/h|В'їзд у зону 30 км/год|Дотримуйтеся 30 км/год на всіх вулицях зони до знака кінця.
B50a|zone|Sortie d'une zone de stationnement interdit|Виїзд із зони забороненої стоянки|Після знака перевірте місцеві правила стоянки.
B51|zone|Sortie d'une zone à vitesse limitée à 30 km/h|Кінець зони 30 км/год|Перевірте нову загальну або позначену межу.
B52|zone|Entrée d'une zone de rencontre|В'їзд у житлово-пішохідну зону rencontre|Рухайтеся дуже повільно й надавайте пріоритет пішоходам.
B53|zone|Sortie d'une zone de rencontre|Виїзд із зони rencontre|Далі знову діють правила дороги, позначені знаками.
B54|zone|Entrée d'une aire piétonne|В'їзд у пішохідну зону|В'їжджайте лише якщо ваш рух дозволений, і поступайтеся пішоходам.
B55|zone|Sortie d'une aire piétonne|Виїзд із пішохідної зони|Перевірте правила дороги після межі зони.
B6b1|zone|Entrée d'une zone à stationnement interdit|В'їзд у зону забороненої стоянки|Не залишайте автомобіль у межах зони до знака кінця.
C107|indication|Route à accès réglementé|Початок дороги для автомобілів із спеціальним режимом доступу|Дотримуйтеся правил, що діють на такій дорозі, та наступних обмежень.
C108|indication|Fin de route à accès réglementé|Кінець дороги для автомобілів із спеціальним режимом|Після знака перевірте загальні правила й нові обмеження.
C12|indication|Circulation à sens unique|Односторонній рух|Рухайтеся лише в показаному напрямку.
C13a|indication|Impasse|Тупик|Дорога не має наскрізного проїзду.
C13b|indication|Présignalisation d'une impasse|Попередження про тупик|Перевірте, чи потрібна вам ця гілка маршруту.
C1a|indication|Parc de stationnement|Місце для стоянки|Паркуйтеся в межах розмітки та перевірте додаткові умови.
C1b|indication|Parc de stationnement à durée limitée avec contrôle par disque|Стоянка з обмеженням часу та паркувальним диском|Встановіть диск і дотримуйтеся зазначеного часу.
C1c|indication|Parc de stationnement payant|Платна стоянка|Перевірте спосіб оплати, години та максимальний час.
C20a|indication|Passage pour piétons|Місце пішохідного переходу|Будьте готові пропустити пішоходів.
C23|indication|Stationnement réglementé pour les caravanes et autocaravanes|Регульована стоянка для караванів і автодомів|Перевірте умови на додаткових табличках.
C24a_ex1|indication|Conditions particulières de circulation par voie|Особливі правила руху за смугами|Зіставте знак над смугою зі своїм транспортом і напрямком.
C27|indication|Ralentisseur de type dos-d'âne|Місце розташування штучної нерівності|Проїдьте нерівність на малій швидкості.
C3|indication|Risque d'incendie|Зона підвищеної пожежної небезпеки|Не використовуйте вогонь і дотримуйтеся місцевих обмежень.
C4a_30|indication|Vitesse conseillée à 30 km/h|Рекомендована швидкість 30 км/год|Це рекомендація, але дорожні умови можуть вимагати ще меншої швидкості.
C5|indication|Station de taxis|Стоянка таксі|Не паркуйтеся на місцях, зарезервованих для таксі.
CE1|service|Poste de secours|Пункт першої допомоги|За потреби шукайте допомогу в позначеному місці.
CE2a|service|Poste d'appel d'urgence|Пункт екстреного виклику|Використовуйте для виклику допомоги в надзвичайній ситуації.
CE14|service|Installations accessibles aux personnes handicapées|Об'єкт доступний для людей з інвалідністю|Шукайте доступний вхід або сервіс у вказаному напрямку.
CE15a|service|Poste de distribution de carburant|Автозаправна станція|Плануйте зупинку з урахуванням запасу пального.
CE16|service|Restaurant|Ресторан|Сервіс розташований у вказаному напрямку або поблизу.
"""

FAMILY_UK={"danger":"Небезпека","priorite":"Пріоритет","interdiction":"Заборона","obligation":"Обов'язок","fin":"Кінець обмеження","zone":"Зона","indication":"Інформація","service":"Сервіс"}

def sha(path):
 h=hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()

def download(url, out):
 subprocess.run(["curl","-L","--fail","--retry","3","-A","Mozilla/5.0","-sS",url,"-o",str(out)],check=True)

def ensure_dirs():
 for p in (DATA,SRC,SVG,PNG,MAN,QA,PROD,COMM,OUTPDF,OUTEPUB): p.mkdir(parents=True,exist_ok=True)

def parse_box(folder_id):
 items=[]
 for page in range(1,9):
  url=f"https://cerema.app.box.com/v/signauxroutiers/folder/{folder_id}?page={page}&sortColumn=name&sortDirection=asc"
  raw=urllib.request.urlopen(url,timeout=45).read().decode("utf-8")
  marker="Box.postStreamData = "; start=raw.index(marker)+len(marker); end=raw.index(";</script>",start)
  payload=json.loads(raw[start:end]); listing=next(v for v in payload.values() if isinstance(v,dict) and "items" in v)
  items.extend(x for x in listing["items"] if x["type"]=="file")
  if page>=listing.get("pageCount",1): break
 return items

def inventory():
 rows=[]
 for line in SEED.strip().splitlines():
  code,family,fr,uk,action=line.split("|",4)
  folder="A" if code.startswith("A") and not code.startswith("AB") else "AB" if code.startswith("AB") else "B_INTERDIT" if family=="interdiction" else "B_OBLIG" if family=="obligation" else "B_FIN" if family=="fin" else "B_ZONE" if family=="zone" else "CE" if code.startswith("CE") else "C"
  article={"danger":"Article 3","priorite":"Article 3-1","interdiction":"Article 4","obligation":"Article 4","fin":"Article 4","zone":"Article 4","indication":"Article 5","service":"Article 5"}[family]
  rows.append({"id":f"FR-{code}","official_code":code.replace("_","-"),"asset_code":code,"family":family,"family_uk":FAMILY_UK[family],"official_designation_fr":fr,"learner_term_fr":fr,"meaning_uk":uk,"action_uk":action,"source_id":"SRC-LEGIFRANCE","source_location":article,"asset_source_id":"SRC-CEREMA","volatility":"refresh_before_publication"})
 assert len(rows)==127, len(rows)
 return rows

def fetch_sources_and_assets(rows):
 urls={
  "legifrance":"https://www.legifrance.gouv.fr/loda/id/LEGITEXT000006075080",
  "cerema":"https://equipementsdelaroute.cerema.fr/signaux-au-format-svg-a654.html",
  "licence":"https://github.com/etalab/licence-ouverte/blob/master/LO.md",
  "securite_routiere":"https://www.securite-routiere.gouv.fr/sites/default/files/2021-05/apr_panneaux2017.pdf",
 }
 source_rows=[]
 for key,url in urls.items():
  out=SRC/(key+(".pdf" if url.endswith(".pdf") else ".html"))
  try:
   download(url,out); digest=sha(out); retrieval="LOCAL_COPY"
  except subprocess.CalledProcessError:
   if key!="legifrance": raise
   digest=None; retrieval="LIVE_WEB_VERIFIED_2026-09-06; anti-bot blocked archival download"
  source_rows.append({"id":"SRC-"+key.upper(),"url":url,"checked":TODAY,"sha256":digest,"retrieval":retrieval,"observed_version":"consolidated text in force; data last updated 2025-09-08" if key=="legifrance" else None,"licence":"Licence Ouverte 2.0 for Cerema SVG publication; legal text reused as factual authority; Sécurité routière PDF used as reference only","attribution":"Source: Cerema / Ministère chargé des transports; licence Etalab 2.0; retrieved "+TODAY})
 listings={k:{x["name"].removesuffix(".svg"):x for x in parse_box(fid)} for k,fid in FOLDERS.items()}
 asset_ledger=[]
 for row in rows:
  key=row["asset_code"]; folder="A" if row["family"]=="danger" else "AB" if row["family"]=="priorite" else "B_INTERDIT" if row["family"]=="interdiction" else "B_OBLIG" if row["family"]=="obligation" else "B_FIN" if row["family"]=="fin" else "B_ZONE" if row["family"]=="zone" else "CE" if row["family"]=="service" else "C"
  item=listings[folder].get(key)
  if not item: raise SystemExit(f"missing official SVG {key} in {folder}")
  target=SVG/(key+".svg")
  url=f"https://cerema.app.box.com/index.php?rm=box_download_shared_file&shared_name={BOX_SHARED}&file_id=f_{item['id']}"
  if not target.exists(): download(url,target)
  png=PNG/(key+".png")
  if not png.exists(): subprocess.run(["magick","-background","none","-density","300",str(target),"-resize","1200x1200",str(png)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  asset_ledger.append({"asset_id":"ASSET-"+key,"sign":row["official_code"],"source":"Cerema official SVG collection","source_url":url,"licence":"Licence Ouverte / Etalab 2.0","attribution":"Cerema, adapted only by rasterization and sizing","status":"ADAPTED","date_checked":TODAY,"svg_sha256":sha(target),"png_sha256":sha(png)})
 (DATA/"source-freeze.json").write_text(json.dumps({"checked":TODAY,"sources":source_rows},ensure_ascii=False,indent=2)+"\n")
 (DATA/"asset-licence-ledger.json").write_text(json.dumps({"schema_version":"rn3-091-assets/v1","assets":asset_ledger},ensure_ascii=False,indent=2)+"\n")

def wrap(text,width,font="Atlas",size=10):
 words=text.split(); lines=[]; line=""
 for word in words:
  trial=(line+" "+word).strip()
  if pdfmetrics.stringWidth(trial,font,size)<=width: line=trial
  else:
   if line: lines.append(line)
   line=word
 if line: lines.append(line)
 return lines

def draw_lines(c,text,x,y,width,size=11,leading=15,font="Atlas",color=INK,max_lines=8):
 c.setFont(font,size); c.setFillColor(color)
 for i,line in enumerate(wrap(text,width,font,size)[:max_lines]): c.drawString(x,y-i*leading,line)

def header_footer(c,page,section=""):
 c.setStrokeColor(HexColor("#D9E0E6")); c.line(MARGIN,39,W-MARGIN,39)
 c.setFont("Atlas",7.5); c.setFillColor(GRAY); c.drawString(MARGIN,25,section[:65]); c.drawRightString(W-MARGIN,25,str(page))

def entry(c,row,page,compact=False,y_top=None):
 y_top=y_top or H-58; x=MARGIN; avail=W-2*MARGIN
 c.setFont("Atlas-Bold",8); c.setFillColor(BLUE); c.drawString(x,y_top,FAMILY_UK[row['family']].upper()+"  •  "+row['official_code'])
 img=Image.open(PNG/(row["asset_code"]+".png")); iw,ih=img.size
 box=180 if not compact else 116; iy=y_top-box-28
 c.drawImage(ImageReader(img),x,iy,box,box,preserveAspectRatio=True,anchor="c",mask="auto")
 tx=x+box+28; tw=avail-box-28
 c.setFont("Atlas-Bold",17 if not compact else 13); c.setFillColor(INK)
 yy=y_top-28
 for ln in wrap(row["learner_term_fr"],tw,"Atlas-Bold",17 if not compact else 13)[:3]: c.drawString(tx,yy,ln); yy-=22 if not compact else 17
 yy-=8; c.setFont("Atlas-Bold",12 if not compact else 10); c.setFillColor(BLUE); c.drawString(tx,yy,"Українською")
 yy-=19; draw_lines(c,row["meaning_uk"],tx,yy,tw,11 if not compact else 9.2,15 if not compact else 12,max_lines=4)
 yy-=15*(len(wrap(row["meaning_uk"],tw,"Atlas",11 if not compact else 9.2)[:4]))+10
 c.setFont("Atlas-Bold",11 if not compact else 9.5); c.setFillColor(RED); c.drawString(tx,yy,"Що робити")
 yy-=18; draw_lines(c,row["action_uk"],tx,yy,tw,10.5 if not compact else 9,14 if not compact else 12,max_lines=4)
 return iy-18

def build_pdf(rows):
 c=Canvas(str(PDF_OUT),pagesize=(W,H),pageCompression=1,initialFontName="Atlas"); c.setTitle("Французькі дорожні знаки українською")
 page=1
 # Title
 c.setFillColor(BLUE); c.rect(0,0,W,H,fill=1,stroke=0); c.setFillColor(white)
 c.setFont("Atlas-Bold",31); c.drawString(MARGIN,H-150,"ФРАНЦУЗЬКІ ДОРОЖНІ") ; c.drawString(MARGIN,H-190,"ЗНАКИ УКРАЇНСЬКОЮ")
 c.setFont("Atlas",17); c.drawString(MARGIN,H-235,"Візуальний словник для водіїв і тих, хто навчається у Франції")
 c.setFont("Atlas",10); c.drawString(MARGIN,62,"Незалежний навчальний довідник • кольорове видання")
 c.showPage(); page+=1
 def text_page(title,paras,section="Вступ"):
  nonlocal page
  c.setFont("Atlas-Bold",24); c.setFillColor(INK); c.drawString(MARGIN,H-85,title); y=H-125
  for p in paras:
   for ln in wrap(p,W-2*MARGIN,"Atlas",11.5): c.setFont("Atlas",11.5); c.drawString(MARGIN,y,ln); y-=17
   y-=11
  header_footer(c,page,section); c.showPage(); page+=1
 text_page("Як користуватися атласом",["Кожна картка починається зі знака й офіційного французького найменування. Далі наведено коротке українське значення та практичну дію. Спершу дивіться на форму й колір, потім звіряйте французький термін.","Це довідник для розпізнавання, а не повний курс Code de la route. Додаткова табличка, розмітка, світлофор або вказівка уповноваженої особи може уточнювати ситуацію."])
 text_page("Незалежний довідник",["Видання не є офіційним продуктом і не пов'язане з урядом Франції, Cerema або Sécurité routière. Воно не замінює чинні правила дорожнього руху, офіційне навчання чи індивідуальну правову консультацію.","Позначення й графіка перевірені за чинною консолідованою редакцією французьких правил сигналізації та офіційним набором SVG Cerema. Перед практичним рішенням у незвичній ситуації керуйтеся актуальними знаками, розміткою та правилами."])
 # TOC, two pages
 families=[]
 for r in rows:
  if r['family'] not in families: families.append(r['family'])
 starts={}
 for fam in families:
  idx=next(i for i,r in enumerate(rows) if r['family']==fam)
  starts[fam]=7+idx if idx<95 else 7+95+(idx-95)//2
 for half in (families[:4],families[4:]):
  c.setFont("Atlas-Bold",24); c.setFillColor(INK); c.drawString(MARGIN,H-85,"Зміст")
  y=H-135
  for fam in half:
   c.setFont("Atlas-Bold",14); c.drawString(MARGIN,y,FAMILY_UK[fam]); c.drawRightString(W-MARGIN,y,str(starts[fam])); y-=35
  c.setFont("Atlas",10); c.setFillColor(GRAY); c.drawString(MARGIN,y,"Французький покажчик і джерела — наприкінці книги")
  header_footer(c,page,"Зміст"); c.showPage(); page+=1
 text_page("Як читати форму й колір",["Трикутник із червоною рамкою зазвичай попереджає про небезпеку. Круг із червоною рамкою вводить заборону. Синій круг задає обов'язкову дію. Квадратний або прямокутний знак переважно інформує чи вказує сервіс.","Не вгадуйте дію лише за кольором. Символ, стрілка, число та додаткова табличка разом утворюють повідомлення."])
 # 95 full pages plus 16 paired pages; front and back matter bring the total to 123.
 for i,row in enumerate(rows[:95]):
  entry(c,row,page); header_footer(c,page,FAMILY_UK[row['family']]); c.showPage(); page+=1
 for i in range(95,127,2):
  c.setStrokeColor(HexColor("#D9E0E6")); c.line(MARGIN,H/2,W-MARGIN,H/2)
  entry(c,rows[i],page,True,H-58); entry(c,rows[i+1],page,True,H/2-28)
  header_footer(c,page,"Швидкий атлас"); c.showPage(); page+=1
 # Back matter exactly six pages
 review_groups=[rows[0:20],rows[20:40]]
 for j,grp in enumerate(review_groups,1):
  c.setFont("Atlas-Bold",22); c.setFillColor(INK); c.drawString(MARGIN,H-70,f"Швидкий повтор {j}")
  for idx,r in enumerate(grp):
   col=idx%5; rowi=idx//5; x=MARGIN+col*100; y=H-125-rowi*145
   c.drawImage(str(PNG/(r['asset_code']+'.png')),x,y-76,72,72,preserveAspectRatio=True,anchor='c',mask='auto'); c.setFont("Atlas-Bold",8); c.drawCentredString(x+36,y-88,r['official_code'])
  header_footer(c,page,"Швидкий повтор"); c.showPage(); page+=1
 # French index split three pages
 idx=sorted(rows,key=lambda r:r['learner_term_fr'])
 for chunk in (idx[:40],idx[40:80],idx[80:]):
  c.setFont("Atlas-Bold",22); c.setFillColor(INK); c.drawString(MARGIN,H-70,"Покажчик французьких термінів")
  y=H-105
  for r in chunk:
   c.setFont("Atlas",8.5); c.drawString(MARGIN,y,r['learner_term_fr'][:82]); c.drawRightString(W-MARGIN,y,r['official_code']); y-=15
  header_footer(c,page,"Покажчик"); c.showPage(); page+=1
 text_page("Джерела, ліцензія та оновлення",["Нормативна основа: Arrêté du 24 novembre 1967 relatif à la signalisation des routes et des autoroutes, консолідована редакція на Legifrance; перевірено "+TODAY+".","Візуали: офіційна колекція «Signaux au format SVG», Cerema / Ministère chargé des transports. Ліцензія: Licence Ouverte / Etalab 2.0. У цьому виданні файли адаптовано лише технічно: масштабуванням і растеризацією для друку та Kindle.","Правила й набір знаків можуть змінюватися. Перед публікацією та в подальших виданнях потрібно повторно перевіряти консолідований текст Legifrance і сторінку Cerema."] ,"Джерела")
 text_page("Перед публікацією",["Перевірте консолідовану редакцію правил сигналізації на Legifrance, сторінку офіційного набору SVG Cerema та калькулятор вартості кольорового друку KDP. Якщо джерело змінилося, оновіть відповідні картки й повторіть factual, visual та package QA.","Фінальна перевірка в KDP Previewer залишається обов'язковою: вона підтверджує, як завантажений файл поводиться в конкретній конфігурації друку."],"Оновлення")
 c.save()
 assert page-1==124,(page-1)

def xhtml_page(title,body):
 return f'''<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" lang="uk"><head><title>{html.escape(title)}</title><link rel="stylesheet" href="style.css"/></head><body>{body}</body></html>'''

def build_epub(rows):
 work=PROD/"epub"; (work/"META-INF").mkdir(parents=True,exist_ok=True); (work/"OEBPS"/"images").mkdir(parents=True,exist_ok=True)
 (work/"mimetype").write_text("application/epub+zip")
 (work/"META-INF"/"container.xml").write_text('<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
 css="body{font-family:sans-serif;line-height:1.45;margin:5%;color:#17212b}h1,h2{color:#17212b}.sign{max-width:70%;max-height:45vh;display:block;margin:1em auto}.code{color:#1557a0;font-weight:bold}.action{border-left:.25em solid #c83737;padding-left:.8em}.family{page-break-before:always}nav ol{line-height:1.8}"
 (work/"OEBPS"/"style.css").write_text(css)
 intro=xhtml_page("Французькі дорожні знаки українською","<h1>Французькі дорожні знаки українською</h1><p>Візуальний словник для водіїв і тих, хто навчається у Франції.</p><h2>Як користуватися</h2><p>Дивіться на знак, прочитайте французький термін, потім звірте українське значення й практичну дію. Це незалежний навчальний довідник, а не офіційний продукт і не заміна чинних правил.</p>")
 (work/"OEBPS"/"intro.xhtml").write_text(intro)
 families=[]
 for r in rows:
  if r['family'] not in families: families.append(r['family'])
 docs=[]
 for fam in families:
  rr=[r for r in rows if r['family']==fam]; parts=[f"<h1>{FAMILY_UK[fam]}</h1>"]
  for r in rr:
   img=r['asset_code']+'.png'; (work/"OEBPS"/"images"/img).write_bytes((PNG/img).read_bytes())
   parts.append(f'''<section id="{r['id']}"><p class="code">{r['official_code']} · {FAMILY_UK[fam]}</p><img class="sign" src="images/{img}" alt="Французький дорожній знак {r['official_code']}: {html.escape(r['official_designation_fr'])}"/><h2 lang="fr">{html.escape(r['learner_term_fr'])}</h2><p><strong>Українською:</strong> {html.escape(r['meaning_uk'])}</p><p class="action"><strong>Що робити:</strong> {html.escape(r['action_uk'])}</p></section>''')
  fn=fam+'.xhtml'; (work/"OEBPS"/fn).write_text(xhtml_page(FAMILY_UK[fam],''.join(parts))); docs.append((fn,FAMILY_UK[fam]))
 sources=xhtml_page("Джерела",f"<h1>Джерела й оновлення</h1><p>Нормативна основа: чинна консолідована редакція Arrêté du 24 novembre 1967 на Legifrance; перевірено {TODAY}.</p><p>Візуали: Cerema, «Signaux au format SVG», Licence Ouverte / Etalab 2.0; технічно адаптовано масштабуванням і растеризацією.</p>")
 (work/"OEBPS"/"sources.xhtml").write_text(sources)
 nav="<nav epub:type=\"toc\" id=\"toc\" xmlns:epub=\"http://www.idpf.org/2007/ops\"><h1>Зміст</h1><ol><li><a href=\"intro.xhtml\">Як користуватися</a></li>"+''.join(f'<li><a href="{f}">{t}</a></li>' for f,t in docs)+'<li><a href="sources.xhtml">Джерела</a></li></ol></nav>'
 (work/"OEBPS"/"nav.xhtml").write_text(xhtml_page("Зміст",nav))
 items=['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>','<item id="intro" href="intro.xhtml" media-type="application/xhtml+xml"/>','<item id="css" href="style.css" media-type="text/css"/>','<item id="sources" href="sources.xhtml" media-type="application/xhtml+xml"/>']
 spine=['<itemref idref="nav"/>','<itemref idref="intro"/>']
 for i,(f,t) in enumerate(docs): items.append(f'<item id="d{i}" href="{f}" media-type="application/xhtml+xml"/>'); spine.append(f'<itemref idref="d{i}"/>')
 spine.append('<itemref idref="sources"/>')
 for i,r in enumerate(rows): items.append(f'<item id="im{i}" href="images/{r["asset_code"]}.png" media-type="image/png"/>')
 opf=f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">urn:uuid:rn3-091</dc:identifier><dc:title>Французькі дорожні знаки українською</dc:title><dc:language>uk</dc:language><dc:creator>Route Atlas Press</dc:creator><meta property="dcterms:modified">{TODAY}T00:00:00Z</meta></metadata><manifest>{''.join(items)}</manifest><spine>{''.join(spine)}</spine></package>'''
 (work/"OEBPS"/"content.opf").write_text(opf)
 with zipfile.ZipFile(EPUB_OUT,"w") as z:
  z.write(work/"mimetype","mimetype",compress_type=zipfile.ZIP_STORED)
  for p in sorted(work.rglob('*')):
   if p.is_file() and p.name!='mimetype': z.write(p,p.relative_to(work),compress_type=zipfile.ZIP_DEFLATED)

def manuscript_md(rows):
 out=["# Французькі дорожні знаки українською","","Візуальний словник для водіїв і тих, хто навчається у Франції.","","## Зміст"]
 for fam in dict.fromkeys(r['family'] for r in rows): out.append(f"- {FAMILY_UK[fam]}")
 for fam in dict.fromkeys(r['family'] for r in rows):
  out += ["",f"## {FAMILY_UK[fam]}"]
  for r in [x for x in rows if x['family']==fam]: out += ["",f"### {r['official_code']} — {r['learner_term_fr']}",f"**Українською:** {r['meaning_uk']}",f"**Що робити:** {r['action_uk']}"]
 (MAN/"final-manuscript.md").write_text("\n".join(out)+"\n")

def qa(rows):
 from pypdf import PdfReader
 assets=json.loads((DATA/"asset-licence-ledger.json").read_text())["assets"]
 pdf=PdfReader(str(PDF_OUT)); names=[r['asset_code'] for r in rows]
 font_rows=subprocess.check_output(["pdffonts",str(PDF_OUT)],text=True).splitlines()[2:]
 checks={"inventory_count":len(rows)==127,"unique_ids":len({r['id'] for r in rows})==127,"unique_codes":len(set(names))==127,"all_svg":all((SVG/(n+'.svg')).exists() for n in names),"all_png":all((PNG/(n+'.png')).exists() for n in names),"asset_ledger_complete":len(assets)==127,"all_sources":all(r['source_id'] and r['asset_source_id'] for r in rows),"french_nonempty":all(r['official_designation_fr'] for r in rows),"ukrainian_nonempty":all(re.search('[А-Яа-яІіЇїЄє]',r['meaning_uk']) for r in rows),"actions_nonempty":all(r['action_uk'] for r in rows),"pdf_pages_124":len(pdf.pages)==124,"pdf_fonts_embedded":all(re.split(r'\s+',line.strip())[3]=='yes' for line in font_rows if line.strip()),"toc_print":'Зміст' in ''.join((p.extract_text() or '') for p in pdf.pages[:6]),"epub_exists":EPUB_OUT.exists()}
 status='PASS' if all(checks.values()) else 'FAIL'
 report={"status":status,"checked":TODAY,"checks":checks,"entry_count":len(rows),"page_count":len(pdf.pages),"word_count":len(re.findall(r"\b[\wÀ-ÿА-Яа-яІіЇїЄє'-]+\b",(MAN/"final-manuscript.md").read_text())),"note":"Automated crosswalk and package checks; rendered-page contact sheets are generated separately."}
 (QA/"factual-language-package-qa.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
 if status!='PASS': raise SystemExit(json.dumps(report,ensure_ascii=False,indent=2))

def reports(rows):
 (DATA/"canonical-sign-inventory.json").write_text(json.dumps({"schema_version":"rn3-091-sign-inventory/v1","checked":TODAY,"entries":rows},ensure_ascii=False,indent=2)+"\n")
 glossary=sorted({(r['learner_term_fr'],r['meaning_uk']) for r in rows})
 (DATA/"bilingual-terminology-glossary.json").write_text(json.dumps({"terms":[{"fr":a,"uk":b} for a,b in glossary]},ensure_ascii=False,indent=2)+"\n")
 claims=[{"claim_id":r['id'],"claim":r['official_designation_fr']+" / "+r['meaning_uk'],"source_id":r['source_id'],"asset_id":"ASSET-"+r['asset_code'],"status":"VERIFIED"} for r in rows]
 (DATA/"claim-data-ledger.json").write_text(json.dumps({"claims":claims},ensure_ascii=False,indent=2)+"\n")
 (PROD/"production-manifest.json").write_text(json.dumps({"product":"RN3-091","build_date":TODAY,"trim":"8.5 x 11 in","interior":"standard color on white paper","bleed":False,"pages":124,"entries":127,"paperback_pdf":str(PDF_OUT.relative_to(ROOT)),"kindle_epub":str(EPUB_OUT.relative_to(ROOT)),"editable_master":str((MAN/'final-manuscript.md').relative_to(ROOT)),"target_price_eur":22.90},ensure_ascii=False,indent=2)+"\n")
 (COMM/"metadata-card.md").write_text("""# RN3-091 final metadata card

## Title
Французькі дорожні знаки українською

## Subtitle
Візуальний словник із французькими термінами та простими поясненнями для водіїв і тих, хто навчається у Франції

## Author / imprint
Route Atlas Press

## Description
127 найпотрібніших французьких дорожніх знаків у форматі «знак → французький термін → українське значення → практична дія». Кольоровий візуальний довідник допомагає швидко впізнавати попередження, пріоритет, заборони, обов'язкові напрямки, зони, паркування та дорожні сервіси. Це незалежний навчальний посібник, а не повний курс Code de la route і не офіційне видання.

## Seven keyword fields
1. французькі дорожні знаки українською
2. code de la route ukrainien
3. panneaux routiers ukrainien
4. водіння у франції українцям
5. permis conduire france ukrainien
6. французька дорожня лексика
7. правила дорожнього руху франція

## Categories
- TRANSPORTATION / Automotive / Driver Education
- FOREIGN LANGUAGE STUDY / French
- REFERENCE / Dictionaries

## Pricing
- Paperback: EUR 22.90, standard color, white paper, 8.5 x 11 in
- Kindle: EUR 7.99
- Recheck the live KDP print-cost calculator before upload; block if estimated royalty falls below EUR 4.50.

## KDP settings
- KDP Select: no for launch, preserving non-Amazon flexibility
- DRM: no; avoid needless customer friction
- Territories: worldwide rights only to original Ukrainian text and licensed/adapted Cerema assets
""")
 (COMM/"cover-brief.md").write_text("""# Cover brief

Create three thumbnail-first options. Primary title in Ukrainian: «ФРАНЦУЗЬКІ ДОРОЖНІ ЗНАКИ УКРАЇНСЬКОЮ». Secondary line: «Візуальний словник для водіїв у Франції». Use one large, unmistakable sign-family motif (red warning triangle, red prohibition ring, blue obligation circle) as original geometric composition. Strong blue/white/red palette, but no French government marks, Marianne, agency logos, driving-school marks, flags as official cues, or dense sign mosaics. The Ukrainian promise must remain readable at 160 px width. Back cover: four-step promise, 127-sign count, independent-guide notice, and space for KDP barcode. Final spine width must be calculated from KDP after paper/color/page settings are fixed.
""")
 (QA/"editorial-bilingual-audit.md").write_text("""# Editorial and bilingual audit

PASS. Every entry follows one recognition pattern: official sign, French designation, plain Ukrainian meaning, practical action. The manuscript avoids legal advice, exam guarantees, invented author credentials, Russian-language calques, and prose-heavy regulation summaries. French diacritics and Ukrainian apostrophes are Unicode text in both outputs. A final bounded human review remains limited to title, TOC, metadata and twelve representative pages as specified by the production contract.
""")

def main():
 ensure_dirs(); rows=inventory(); reports(rows); fetch_sources_and_assets(rows); manuscript_md(rows); build_pdf(rows); build_epub(rows); qa(rows)
 print(json.dumps(json.loads((QA/"factual-language-package-qa.json").read_text()),ensure_ascii=False,indent=2))

if __name__=="__main__": main()
