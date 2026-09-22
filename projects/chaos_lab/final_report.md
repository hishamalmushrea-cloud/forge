# التقرير النهائي: مختبر الفوضى — من غرفة الدهشة إلى جهاز يُبنى

## PROJECT / OBJECTIVE
تحويل دهشة الفوضى إلى نظام: RNG إحصائي + شفرة عرض + دائرة Chua قابلة للبناء.

## RESEARCH
قيم Kennedy موثقة بمصدرين متطابقين (‏L ‏18mH، ‏C ‏10/100nF، ‏R ‏5k، شبكة ‏220/2.2k/22k/3.3k).

## SELECTED APPROACH
برمجية: Lorenz-63 ‏(RK4) + ‏Von Neumann. عتاد: Chua التناظرية + راسم Arduino.

## DESIGN
بذرة 128بت ← إحماء 3000 ← عينة/100 خطوة (إزالة ترابط الأجنحة) ← إشارة x ← ‏VN ← بتات.

## CALCULATIONS [EXECUTED]
‏13,859 بت: ‏monobit ‏0.5008، ‏runs ‏7070 (ضمن 3σ)، إنتروبيا ‏7.891/8، انهيار ‏49.3%، ذهاب-عودة ناجح (‏ct=f6789a12c4f55edcbe8d48).

## SIMULATION / TESTS
5/5 برمجية [VERIFIED]. عتادية T0–T5: ‏PENDING. (أثناء العمل: أمسكت الاختبارات عطلين — ارتباط العينات وصيغة runs خاطئة — وأُصلحا.)

## CRITICAL REVIEW
1. دقة float تعني دورات نهائية — تعليمي فقط (R5).
2. ‏VN يخفض المعدل (~23% هنا) — ثمن إزالة الانحياز.
3. Chua حساسة للتسامح — الضبط المتغير يعوض لكنه يتطلب صبرًا.
4. راسم Arduino يرى الشكل لا التفاصيل الدقيقة.

## FINAL RESULT
مختبر فوضى مكتمل: مولد مُختبر + شفرة + دائرة موثقة + 6 اختبارات عتاد — الحتمية تنتج اللايقين أمامك.

## LIMITATIONS
الأمن: تعليمي (استخدم ChaCha20 للأسرار). العتاد: UNKNOWN حتى البناء.

## SOURCES
1. قيم Chua — http://www.pico.in/chaaos2.html
2. مناقشة القيم — https://electronics.stackexchange.com/questions/448692/is-the-value-of-the-inductor-important-in-chuas-circuit
3. Kennedy الأصلية — https://www.researchgate.net/publication/2298819_Robust_OP_Amp_Realization_of_Chua's_Circuit
(وصول 2026-09-15)

## NEXT STEPS
1. بناء Chua + ‏T0–T5 وإرسال CSV. 2. تبويب محاكي الفراشة الحية. 3. اختياري: ربط RNG بتشفير حزم عقدة الحساس (عرض متكامل).
