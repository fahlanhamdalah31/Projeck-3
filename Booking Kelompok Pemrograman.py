import sqlite3
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

DB_NAME = "hotel_emerald.db"
TAX_RATE = 0.10

# List + Dict
ROOMS = [
    {"id": "ST01", "name": "Emerald Standard", "type": "Standard", "price": 450000, "max_guest": 2},
    {"id": "DL01", "name": "Deluxe Garden", "type": "Deluxe", "price": 750000, "max_guest": 3},
    {"id": "EX01", "name": "Executive King", "type": "Executive", "price": 1150000, "max_guest": 3},
    {"id": "SU01", "name": "Emerald Suite", "type": "Suite", "price": 1850000, "max_guest": 4},
]

# Tuple + Set
PAYMENTS = ("Transfer Bank", "E-Wallet", "Kartu Kredit", "Bayar di Hotel")
ROOM_TYPES = sorted({room["type"] for room in ROOMS})


def rupiah(n):
    return "Rp " + f"{int(n):,}".replace(",", ".")


def parse_date(text):
    return datetime.strptime(text, "%Y-%m-%d").date()


def hitung_malam(check_in, check_out):
    return (parse_date(check_out) - parse_date(check_in)).days


def buat_id():
    return "EM" + datetime.now().strftime("%H%M%S")


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row
        self.buat_tabel()
        self.isi_kamar_awal()

    def buat_tabel(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                price INTEGER,
                max_guest INTEGER
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id TEXT PRIMARY KEY,
                room_id TEXT,
                guest_name TEXT,
                phone TEXT,
                email TEXT,
                check_in TEXT,
                check_out TEXT,
                nights INTEGER,
                guests INTEGER,
                payment TEXT,
                total INTEGER,
                status TEXT,
                created_at TEXT
            )
        """)
        self.conn.commit()

    def isi_kamar_awal(self):
        for room in ROOMS:
            self.conn.execute("""
                INSERT OR IGNORE INTO rooms VALUES (?, ?, ?, ?, ?)
            """, (room["id"], room["name"], room["type"], room["price"], room["max_guest"]))
        self.conn.commit()

    def ambil_kamar(self, tipe="Semua"):
        if tipe == "Semua":
            rows = self.conn.execute("SELECT * FROM rooms ORDER BY price").fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM rooms WHERE type=? ORDER BY price", (tipe,)).fetchall()
        return [dict(row) for row in rows]

    def ambil_kamar_id(self, room_id):
        row = self.conn.execute("SELECT * FROM rooms WHERE id=?", (room_id,)).fetchone()
        return dict(row) if row else None

    def tambah_reservasi(self, data):
        self.conn.execute("""
            INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["id"], data["room_id"], data["guest_name"], data["phone"],
            data["email"], data["check_in"], data["check_out"], data["nights"],
            data["guests"], data["payment"], data["total"], data["status"],
            data["created_at"]
        ))
        self.conn.commit()

    def ambil_reservasi(self, status="Semua"):
        query = """
            SELECT b.*, r.name AS room_name
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
        """
        if status == "Semua":
            rows = self.conn.execute(query + " ORDER BY created_at DESC").fetchall()
        else:
            rows = self.conn.execute(query + " WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
        return [dict(row) for row in rows]

    def ubah_status(self, booking_id, status):
        self.conn.execute("UPDATE bookings SET status=? WHERE id=?", (status, booking_id))
        self.conn.commit()

    def hapus_reservasi(self, booking_id):
        self.conn.execute("DELETE FROM bookings WHERE id=?", (booking_id,))
        self.conn.commit()


class HotelApp:
    def __init__(self, root):
        self.root = root
        self.db = Database()
        self.selected_room = None

        self.root.title("Hotel Emerald Ln - Sistem Reservasi")
        self.root.geometry("1050x650")
        self.root.configure(bg="#f7f6f3")

        self.buat_tampilan()
        self.tampilkan_kamar()
        self.tampilkan_reservasi()

    def buat_tampilan(self):
        header = tk.Frame(self.root, bg="#1a3d2b", height=70)
        header.pack(fill="x")
        tk.Label(header, text="Hotel Emerald Ln", bg="#1a3d2b", fg="white",
                 font=("Segoe UI", 20, "bold")).pack(side="left", padx=20, pady=15)

        main = ttk.Notebook(self.root)
        main.pack(fill="both", expand=True, padx=15, pady=15)

        self.tab_kamar = ttk.Frame(main)
        self.tab_admin = ttk.Frame(main)
        main.add(self.tab_kamar, text="Kamar")
        main.add(self.tab_admin, text="Reservasi Admin")

        self.buat_tab_kamar()
        self.buat_tab_admin()

    def buat_tab_kamar(self):
        filter_frame = ttk.Frame(self.tab_kamar)
        filter_frame.pack(fill="x", pady=10)

        ttk.Label(filter_frame, text="Tipe kamar").pack(side="left")
        self.tipe_var = tk.StringVar(value="Semua")
        ttk.Combobox(filter_frame, textvariable=self.tipe_var,
                     values=["Semua"] + ROOM_TYPES, state="readonly").pack(side="left", padx=8)
        ttk.Button(filter_frame, text="Cari", command=self.tampilkan_kamar).pack(side="left")

        self.table_kamar = ttk.Treeview(
            self.tab_kamar,
            columns=("id", "name", "type", "price", "guest"),
            show="headings",
            height=7
        )
        for col, title in {
            "id": "ID", "name": "Nama Kamar", "type": "Tipe",
            "price": "Harga/Malam", "guest": "Max Tamu"
        }.items():
            self.table_kamar.heading(col, text=title)
        self.table_kamar.pack(fill="x", pady=10)
        self.table_kamar.bind("<<TreeviewSelect>>", self.pilih_kamar)

        form = ttk.LabelFrame(self.tab_kamar, text="Form Reservasi")
        form.pack(fill="x", pady=10)

        self.nama = tk.StringVar()
        self.hp = tk.StringVar()
        self.email = tk.StringVar()
        self.check_in = tk.StringVar(value=date.today().isoformat())
        self.check_out = tk.StringVar(value=(date.today() + timedelta(days=1)).isoformat())
        self.tamu = tk.StringVar(value="2")
        self.bayar = tk.StringVar(value=PAYMENTS[0])

        fields = [
            ("Nama", self.nama), ("No HP", self.hp), ("Email", self.email),
            ("Check-in YYYY-MM-DD", self.check_in), ("Check-out YYYY-MM-DD", self.check_out),
            ("Jumlah Tamu", self.tamu)
        ]

        for i, (label, var) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i // 3 * 2, column=i % 3, sticky="w", padx=8, pady=4)
            ttk.Entry(form, textvariable=var, width=30).grid(row=i // 3 * 2 + 1, column=i % 3, padx=8, pady=4)

        ttk.Label(form, text="Pembayaran").grid(row=4, column=0, sticky="w", padx=8)
        ttk.Combobox(form, textvariable=self.bayar, values=PAYMENTS, state="readonly").grid(row=5, column=0, padx=8)

        self.total_label = ttk.Label(form, text="Total: -", font=("Segoe UI", 11, "bold"))
        self.total_label.grid(row=5, column=1)

        ttk.Button(form, text="Hitung Total", command=self.hitung_total).grid(row=5, column=2, padx=8)
        ttk.Button(form, text="Simpan Reservasi", command=self.simpan_reservasi).grid(row=6, column=0, columnspan=3, sticky="ew", padx=8, pady=10)

    def buat_tab_admin(self):
        top = ttk.Frame(self.tab_admin)
        top.pack(fill="x", pady=10)

        self.status_var = tk.StringVar(value="Semua")
        ttk.Combobox(top, textvariable=self.status_var,
                     values=["Semua", "pending", "confirmed", "cancelled"],
                     state="readonly").pack(side="left")
        ttk.Button(top, text="Filter", command=self.tampilkan_reservasi).pack(side="left", padx=5)
        ttk.Button(top, text="ACC", command=lambda: self.ubah_status("confirmed")).pack(side="right", padx=5)
        ttk.Button(top, text="Tolak", command=lambda: self.ubah_status("cancelled")).pack(side="right", padx=5)
        ttk.Button(top, text="Hapus", command=self.hapus).pack(side="right", padx=5)

        self.table_res = ttk.Treeview(
            self.tab_admin,
            columns=("id", "guest", "room", "in", "out", "night", "total", "status"),
            show="headings"
        )
        for col, title in {
            "id": "ID", "guest": "Tamu", "room": "Kamar", "in": "Check-in",
            "out": "Check-out", "night": "Malam", "total": "Total", "status": "Status"
        }.items():
            self.table_res.heading(col, text=title)
        self.table_res.pack(fill="both", expand=True)

    def tampilkan_kamar(self):
        for item in self.table_kamar.get_children():
            self.table_kamar.delete(item)
        for room in self.db.ambil_kamar(self.tipe_var.get()):
            self.table_kamar.insert("", "end", iid=room["id"],
                                    values=(room["id"], room["name"], room["type"], rupiah(room["price"]), room["max_guest"]))

    def pilih_kamar(self, event=None):
        selected = self.table_kamar.selection()
        self.selected_room = self.db.ambil_kamar_id(selected[0]) if selected else None
        self.hitung_total(False)

    def hitung_total(self, warning=True):
        if not self.selected_room:
            self.total_label.config(text="Total: pilih kamar dulu")
            return None
        try:
            malam = hitung_malam(self.check_in.get(), self.check_out.get())
            if malam <= 0:
                raise ValueError
            subtotal = self.selected_room["price"] * malam
            total = subtotal + round(subtotal * TAX_RATE)
            self.total_label.config(text=f"Total: {rupiah(total)} ({malam} malam)")
            return total
        except ValueError:
            self.total_label.config(text="Total: tanggal salah")
            if warning:
                messagebox.showerror("Error", "Tanggal harus benar dan check-out setelah check-in.")
            return None

    def simpan_reservasi(self):
        if not self.selected_room:
            messagebox.showerror("Error", "Pilih kamar dulu.")
            return
        if len(self.nama.get().strip()) < 3:
            messagebox.showerror("Error", "Nama minimal 3 huruf.")
            return
        if not self.hp.get().startswith("08") or not self.hp.get().isdigit():
            messagebox.showerror("Error", "No HP harus angka dan diawali 08.")
            return
        if "@" not in self.email.get():
            messagebox.showerror("Error", "Email tidak valid.")
            return

        total = self.hitung_total(False)
        malam = hitung_malam(self.check_in.get(), self.check_out.get())
        tamu = int(self.tamu.get())

        if tamu > self.selected_room["max_guest"]:
            messagebox.showerror("Error", "Jumlah tamu melebihi batas kamar.")
            return

        data = {
            "id": buat_id(),
            "room_id": self.selected_room["id"],
            "guest_name": self.nama.get(),
            "phone": self.hp.get(),
            "email": self.email.get(),
            "check_in": self.check_in.get(),
            "check_out": self.check_out.get(),
            "nights": malam,
            "guests": tamu,
            "payment": self.bayar.get(),
            "total": total,
            "status": "pending",
            "created_at": datetime.now().isoformat(timespec="seconds")
        }

        self.db.tambah_reservasi(data)
        messagebox.showinfo("Sukses", "Reservasi berhasil disimpan.")
        self.tampilkan_reservasi()

    def tampilkan_reservasi(self):
        for item in self.table_res.get_children():
            self.table_res.delete(item)
        for res in self.db.ambil_reservasi(self.status_var.get()):
            self.table_res.insert("", "end", iid=res["id"],
                                  values=(res["id"], res["guest_name"], res["room_name"],
                                          res["check_in"], res["check_out"], res["nights"],
                                          rupiah(res["total"]), res["status"]))

    def selected_reservasi(self):
        selected = self.table_res.selection()
        if not selected:
            messagebox.showwarning("Pilih data", "Pilih reservasi dulu.")
            return None
        return selected[0]

    def ubah_status(self, status):
        booking_id = self.selected_reservasi()
        if booking_id:
            self.db.ubah_status(booking_id, status)
            self.tampilkan_reservasi()

    def hapus(self):
        booking_id = self.selected_reservasi()
        if booking_id and messagebox.askyesno("Hapus", "Yakin hapus reservasi ini?"):
            self.db.hapus_reservasi(booking_id)
            self.tampilkan_reservasi()


root = tk.Tk()
app = HotelApp(root)
root.mainloop()