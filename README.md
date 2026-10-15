# Student Budget Tracker (Python)

เว็บแอปภาษาไทยสำหรับจดรายรับรายจ่ายนักศึกษา สร้างด้วย Streamlit และ SQLite

## ความสามารถ

- เพิ่มและลบรายการรายรับหรือรายจ่าย พร้อมหมวดหมู่ วันที่ และบันทึกช่วยจำ
- ดูยอดรายรับ รายจ่าย และยอดคงเหลือแยกตามเดือน
- ตั้งงบรายเดือน และแจ้งเตือนเมื่อใช้ถึง 80% หรือเกินงบ
- ดูกราฟรายจ่ายตามหมวดหมู่ และกรองรายการ
- ดาวน์โหลดรายการของเดือนที่เลือกเป็น CSV
- เก็บข้อมูลใน SQLite

## รันบนเครื่อง

ต้องมี Python 3.10 ขึ้นไป

```bash
python -m venv .venv
```

เปิด virtual environment แล้วติดตั้งแพ็กเกจและเปิดแอป:

```bash
pip install -r requirements.txt
streamlit run app.py
.\.venv\Scripts\python.exe -m streamlit run app.py
```

เบราว์เซอร์จะเปิดแอปที่ `http://localhost:8501` โดยอัตโนมัติ

## อัปขึ้น GitHub และ Deploy

GitHub Pages ไม่ได้รัน Python backend โดยตรง โปรเจกต์นี้จึงใช้ Streamlit Community Cloud ซึ่งเชื่อมกับ GitHub Repository ได้

1. สร้าง repository ใหม่บน GitHub
2. อัปโหลดไฟล์ทั้งหมดในโฟลเดอร์นี้ไปไว้ที่ root ของ repository
3. เปิด [share.streamlit.io](https://share.streamlit.io/) แล้วเชื่อมบัญชี GitHub
4. เลือก **Create app** แล้วเลือก repository, branch และไฟล์ `app.py`
5. ใน Advanced settings เลือก Python 3.12 แล้วกด Deploy

เมื่อ push การแก้ไขไปยัง branch ที่เลือก Streamlit Community Cloud จะอัปเดตแอปจาก repository

## ข้อจำกัดของต้นแบบ

- ไม่มีระบบสมัครสมาชิก แอปแยกข้อมูลตามเซสชันของเบราว์เซอร์ เพื่อไม่ให้ผู้เข้าชมเห็นรายการของเซสชันอื่น
- หากปิดเซสชันหรือเริ่มเซสชันใหม่ อาจเข้าถึงข้อมูลเดิมไม่ได้ แม้ข้อมูลยังอยู่ใน SQLite
- SQLite บน Streamlit Community Cloud ใช้พื้นที่ไฟล์ของแอป ซึ่งไม่เหมาะเป็นที่เก็บข้อมูลถาวรหรือข้อมูลการเงินจริง หากต้องใช้จริงควรเพิ่มระบบเข้าสู่ระบบและฐานข้อมูลที่มี persistent storage เช่น PostgreSQL
- เวอร์ชัน Community Cloud ที่ deploy จาก repository เดียวกันอาจใช้ไฟล์ SQLite ร่วมกันบนเซิร์ฟเวอร์ แต่แต่ละเซสชันถูกกรองด้วยรหัสสุ่มในหน่วยความจำ
- ไม่ควรใช้บันทึกข้อมูลการเงินที่เป็นความลับในต้นแบบสาธารณะนี้
