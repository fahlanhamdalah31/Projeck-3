import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

DB_NAME = "hotel_emerald.db"


def rupiah(n):
    return "Rp " + f"{int(n):,}".replace(",", ".")


class AdminApp:
    def __init__(self, root):
        self.root = root
        self.conn = sqlite3.connect(DB_NAME)
        self.conn.row_factory = sqlite3.Row

        self.root.title("Admin - Hotel Emerald Ln")
        self.root.geometry("1050x600")

        self.status_var = tk.StringVar(value="Semua")
        self.buat_tampilan()
        self.tampilkan_data()

    def buat_tampilan(self):
        header = tk.Frame(self.root, bg="#1a3d2b", height=70)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Admin Reservasi Hotel Emerald Ln",
            bg="#1a3d2b",
            fg="white",
            font=("Segoe UI", 18, "bold")
        ).pack(side="left", padx=20, pady=15)

        kontrol = ttk.Frame(self.root)
        kontrol.pack(fill="x", padx=15, pady=10)

        ttk.Label(kontrol, text="Filter Status").pack(side="left")

        ttk.Combobox(
            kontrol,
            textvariable=self.status_var,
            values=["Semua", "pending", "confirmed", "cancelled"],
            state="readonly",
            width=20
        ).pack(side="left", padx=8)

        ttk.Button(kontrol, text="Tampilkan", command=self.tampilkan_data).pack(side="left")
        ttk.Button(kontrol, text="ACC", command=lambda: self.ubah_status("confirmed")).pack(side="right", padx=5)
        ttk.Button(kontrol, text="Tolak", command=lambda: self.ubah_status("cancelled")).pack(side="right", padx=5)
        ttk.Button(kontrol, text="Hapus", command=self.hapus_data).pack(side="right", padx=5)

        self.info_label = ttk.Label(self.root, text="", font=("Segoe UI", 11, "bold"))
        self.info_label.pack(anchor="w", padx=15, pady=5)

        self.tabel = ttk.Treeview(
            self.root,
            columns=("id", "nama", "hp", "kamar", "checkin", "checkout", "malam", "total", "status"),
            show="headings"
        )

        judul = {
            "id": "ID",
            "nama": "Nama Tamu",
            "hp": "No HP",
            "kamar": "Kamar",
            "checkin": "Check-In",
            "checkout": "Check-Out",
            "malam": "Malam",
            "total": "Total",
            "status": "Status"
        }

        for kolom, teks in judul.items():
            self.tabel.heading(kolom, text=teks)
            self.tabel.column(kolom, width=110)

        self.tabel.pack(fill="both", expand=True, padx=15, pady=10)

    def ambil_data(self):
        status = self.status_var.get()

        query = """
            SELECT b.*, r.name AS room_name
            FROM bookings b
            JOIN rooms r ON r.id = b.room_id
        """

        if status == "Semua":
            return self.conn.execute(query + " ORDER BY created_at DESC").fetchall()

        return self.conn.execute(
            query + " WHERE b.status = ? ORDER BY created_at DESC",
            (status,)
        ).fetchall()

    def tampilkan_data(self):
        for item in self.tabel.get_children():
            self.tabel.delete(item)

        data = self.ambil_data()

        total_reservasi = 0
        total_pending = 0
        total_confirmed = 0
        total_cancelled = 0
        pendapatan = 0

        for row in data:
            total_reservasi += 1

            if row["status"] == "pending":
                total_pending += 1
            elif row["status"] == "confirmed":
                total_confirmed += 1
                pendapatan += row["total"]
            elif row["status"] == "cancelled":
                total_cancelled += 1

            self.tabel.insert(
                "",
                "end",
                iid=row["id"],
                values=(
                    row["id"],
                    row["guest_name"],
                    row["phone"],
                    row["room_name"],
                    row["check_in"],
                    row["check_out"],
                    row["nights"],
                    rupiah(row["total"]),
                    row["status"]
                )
            )

        self.info_label.config(
            text=f"Total: {total_reservasi} | Pending: {total_pending} | "
                 f"Confirmed: {total_confirmed} | Cancelled: {total_cancelled} | "
                 f"Pendapatan: {rupiah(pendapatan)}"
        )

    def pilih_id(self):
        selected = self.tabel.selection()

        if not selected:
            messagebox.showwarning("Belum dipilih", "Pilih data reservasi dulu.")
            return None

        return selected[0]

    def ubah_status(self, status_baru):
        booking_id = self.pilih_id()

        if booking_id is None:
            return

        self.conn.execute(
            "UPDATE bookings SET status = ? WHERE id = ?",
            (status_baru, booking_id)
        )
        self.conn.commit()

        messagebox.showinfo("Berhasil", f"Reservasi {booking_id} diubah menjadi {status_baru}.")
        self.tampilkan_data()

    def hapus_data(self):
        booking_id = self.pilih_id()

        if booking_id is None:
            return

        yakin = messagebox.askyesno("Konfirmasi", f"Yakin ingin hapus reservasi {booking_id}?")

        if yakin:
            self.conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            self.conn.commit()
            messagebox.showinfo("Berhasil", "Data reservasi berhasil dihapus.")
            self.tampilkan_data()


root = tk.Tk()
app = AdminApp(root)
root.mainloop()
