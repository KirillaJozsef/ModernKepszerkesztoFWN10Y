Modern Képszerkesztő Használati Útmutató

Verzió: 3.13
Készítette: Kirilla József, Neptun kód: FWN10Y

Bevezetés
Ez a program egy modern, képszerkesztő alkalmazás Python 3.13 alatt, amely a CustomTkinter és OpenCV könyvtárakat használja. Lehetővé teszi képek szerkesztését valós idejű előnézettel, különböző transzformációkkal és szűrőkkel.

Telepítés
A program futtatásához szükséges Python 3.13 és az alábbi csomagok telepítése:

pip install customtkinter pillow opencv-python numpy

Főbb funkciók
•	Kép megnyitása és mentése különböző formátumokban (PNG, JPG, BMP).
•	Valós idejű előnézet minden változtatásnál (forgatás, flip, fényerő, kontraszt, blur, filterek).
•	Forgatás csúszkával (-180°..180°).
•	Flip H/V csúszkával (0/1 toggle).
•	Átméretezés megadott szélességre és magasságra.
•	Kép kivágása (Crop) kijelöléssel.
•	Szűrők kiválasztása legördülő menüből: None, Grayscale, Blur, Canny, Emboss, Sepia.
•	Undo / Redo funkció a módosítások visszavonásához és visszaállításához.
•	Commit gomb a módosítások rögzítéséhez a history listába.
•	Reset gomb az eredeti kép visszaállításához.

Használati útmutató
Kép megnyitása
1. Kattints a 'Megnyitás' gombra a bal oldali panelen.
2. Válassz egy képfájlt (.jpg, .png, .bmp, .tiff) a számítógépedről.
3. A kép megjelenik a jobb oldali előnézeti ablakban.

Kép mentése
1. Kattints a 'Mentés' gombra.
2. Válaszd ki a mentés helyét és fájlformátumot.
3. A kép elmentődik az adott útvonalra.
Undo / Redo
1. Minden fontos változtatás után nyomd meg a 'Commit' gombot, hogy a módosítások elmentődjenek a history-be.
2. A 'Visszavonás (undo)' gomb az utolsó commit-olt állapotot állítja vissza.
3. A 'Mégis (redo)' gomb visszaállítja az Undo előtti állapotot.

Transzformációk és effektek
1. Forgatás: csúszkával állítható -180° és 180° között.
2. Flip H/V: csúszkával állítható 0 (nem) és 1 (igen).
3. Fényerő és kontraszt: csúszkákkal állítható.
4. Blur: csúszkával állítható Gauss elmosás.
5. Filterek: legördülő menüből választható szűrő.
6. Resize: írd be a kívánt szélességet és magasságot, majd kattints az 'Átméretez' gombra.
7. Crop: kattints a 'Crop' gombra, jelöld ki a területet az egérrel, majd engedd el.
Commit funkció
A 'Commit (mentés history-be)' gomb rögzíti a jelenlegi állapotot a history listába. Ez lehetővé teszi az Undo/Redo funkció használatát a későbbi módosításokhoz.
Reset
A 'Reset (eredeti)' gomb visszaállítja a kép eredeti állapotát, és törli az Undo/Redo stack-et.
