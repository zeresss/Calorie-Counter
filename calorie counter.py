import sys
import sqlite3
import csv

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox


class CalorieCounter(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('./source/calorie counter.ui', self)

        self.con = sqlite3.connect('./source/calorie counter db.db')
        cur = self.con.cursor()

        row = cur.execute('SELECT * FROM user').fetchone()
        self.calorie_norm, self.protein_norm, self.fat_norm, self.carbohydrate_norm = row
        self.total_calorie, self.total_protein, self.total_fat, self.total_carbohydrate = 0, 0, 0, 0

        dates = cur.execute('SELECT date FROM dates').fetchall()
        for i in dates:
            self.text.appendPlainText(i[0])
            food = cur.execute('SELECT name FROM food WHERE date_id = (SELECT id FROM dates WHERE id = date_id)')
            for j in food:
                self.text.appendPlainText(j[0])

        with open('./source/list of food.csv', encoding='utf8') as file:
            reader = csv.reader(file, delimiter=',')
            food = cur.execute('SELECT name, amount FROM food')
            for i in food:
                for j in list(reader)[1:]:
                    if i[0] == j[0]:
                        self.total_calorie += round(float(j[4]) / 100 * i[1])
                        self.total_protein += round(float(j[1]) / 100 * i[1])
                        self.total_fat += round(float(j[2]) / 100 * i[1])
                        self.total_carbohydrate += round(float(j[3]) / 100 * i[1])

        dates = len(dates)
        if not dates:
            dates = 1
        else:
            self.add_day_btn.setEnabled(True)
            self.add_product_btn.setEnabled(True)
        self.statistics.setText(
            f'Калории (ккал): Рекомендуемые в день - {self.calorie_norm}, '
            f'Средние в день - {round(self.total_calorie / dates)};\n'
            f'Белки (г): Рекомендуемые в день - {self.protein_norm}, '
            f'Средние в день - {round(self.total_protein / dates)};\n'
            f'Жиры (г): Рекомендуемые в день - {self.fat_norm}, '
            f'Средние в день - {round(self.total_fat / dates)};\n'
            f'Углеводы (г): Рекомендуемые в день - {self.carbohydrate_norm}, '
            f'Средние в день - {round(self.total_carbohydrate / dates)}')

        self.add_day_btn.clicked.connect(self.add_day)
        self.add_product_btn.clicked.connect(self.add_product)
        self.edit_characteristics_btn.clicked.connect(self.edit_characteristics)

    def add_day(self):
        dialog = DayAddDialog()
        dialog.exec()

        if dialog.clicked:
            self.text.setPlainText('')

            cur = self.con.cursor()
            dates = cur.execute('SELECT date FROM dates').fetchall()
            if dialog.date not in map(lambda x: x[0], dates):
                cur.execute(f'INSERT INTO dates(date) VALUES("{dialog.date}")')
                self.con.commit()

            dates = cur.execute('SELECT date FROM dates').fetchall()
            for i in dates:
                self.text.appendPlainText(i[0])
                food = cur.execute(
                    f'SELECT name FROM food WHERE date_id = (SELECT id FROM dates WHERE date = "{i[0]}")').fetchall()
                for j in food:
                    self.text.appendPlainText(j[0])

            cur.close()

        self.add_product_btn.setEnabled(True)

    def add_product(self):
        dialog = ProductAddDialog()
        dialog.exec()

        if dialog.clicked:
            self.text.setPlainText('')

            with open('./source/list of food.csv', encoding='utf8') as file:
                reader = csv.reader(file, delimiter=',')
                for i in list(reader)[1:]:
                    if i[0] == dialog.product:
                        product = i
                        break
                self.total_calorie += round(float(product[4]) / 100 * dialog.amount)
                self.total_protein += round(float(product[1]) / 100 * dialog.amount)
                self.total_fat += round(float(product[2]) / 100 * dialog.amount)
                self.total_carbohydrate += round(float(product[3]) / 100 * dialog.amount)

            cur = self.con.cursor()
            cur.execute(
                f'INSERT INTO food(date_id, name, amount) VALUES((SELECT id FROM dates WHERE date = "{dialog.day}"), '
                f'"{product[0]}", {dialog.amount})')
            self.con.commit()

            dates = cur.execute('SELECT date FROM dates').fetchall()
            for i in dates:
                self.text.appendPlainText(i[0])
                food = cur.execute(
                    f'SELECT name FROM food WHERE date_id = (SELECT id FROM dates WHERE date = "{i[0]}")').fetchall()
                for j in food:
                    self.text.appendPlainText(j[0])

            dates = len(dates)
            self.statistics.setText(
                f'Калории (ккал): Рекомендуемые в день - {self.calorie_norm}, '
                f'Средние в день - {round(self.total_calorie / dates)};\n'
                f'Белки (г): Рекомендуемые в день - {self.protein_norm}, '
                f'Средние в день - {round(self.total_protein / dates)};\n'
                f'Жиры (г): Рекомендуемые в день - {self.fat_norm}, '
                f'Средние в день - {round(self.total_fat / dates)};\n'
                f'Углеводы (г): Рекомендуемые в день - {self.carbohydrate_norm}, '
                f'Средние в день - {round(self.total_carbohydrate / dates)}')

            cur.close()

    def edit_characteristics(self):
        dialog = EditCharacteristicsDialog()
        dialog.exec()

        if dialog.clicked:
            self.calorie_norm = round(dialog.calorie)
            self.protein_norm = round(dialog.protein)
            self.fat_norm = round(dialog.fat)
            self.carbohydrate_norm = round(dialog.carbohydrate)
            self.con.cursor().execute(
                f'UPDATE user SET calorie_norm = {self.carbohydrate_norm}, protein_norm = {self.protein_norm}, '
                f'fat_norm = {self.fat_norm}, carbohydrate_norm = {self.carbohydrate_norm}')

        days = len(self.con.cursor().execute('SELECT date FROM dates').fetchall())
        if not days:
            days = 1
        self.statistics.setText(
            f'Калории (ккал): Общие - {self.total_calorie}, Рекомендуемые в день - {self.calorie_norm}, '
            f'Средние в день - {round(self.total_calorie / days)}\n'
            f'Белки (г): Общие - {self.total_protein}, Рекомендуемые в день - {self.protein_norm}, '
            f'Средние в день - {round(self.total_protein / days)}\n'
            f'Жиры (г): Общие - {self.total_fat}, Рекомендуемые в день - {self.fat_norm}, '
            f'Средние в день - {round(self.total_fat / days)}\n'
            f'Углеводы (г): Общие - {self.total_carbohydrate}, Рекомендуемые в день - {self.carbohydrate_norm}, '
            f'Средние в день - {round(self.total_carbohydrate / days)}')

        self.add_day_btn.setEnabled(True)

    def closeEvent(self, event):
        dialog = ExitDialog()
        dialog.exec()

        if dialog.no_clicked:
            cur = self.con.cursor()
            cur.execute('DELETE FROM dates')
            cur.execute('DELETE FROM food')
            cur.execute('UPDATE user SET calorie_norm = 0, protein_norm = 0, fat_norm = 0, carbohydrate_norm = 0')
            self.con.commit()
            self.con.close()
        event.accept()


class DayAddDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('./source/day add dialog.ui', self)
        self.clicked = False
        self.add_btn.clicked.connect(self.click)

    def click(self):
        self.clicked = True
        self.date = self.calendar.selectedDate().toString('dd/MM/yyyy')
        self.close()


class ProductAddDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('./source/product add dialog.ui', self)

        self.clicked = False
        self.con = sqlite3.connect('./source/calorie counter db.db')

        with open('./source/list of food.csv', encoding='utf8') as file:
            reader = map(lambda x: x[0], list(csv.reader(file, delimiter=','))[1:])
            self.product_combo_box.addItems(list(reader))

        dates = map(lambda x: x[0], self.con.cursor().execute('SELECT date FROM dates').fetchall())
        self.day_combo_box.addItems(dates)

        self.add_btn.clicked.connect(self.click)
        self.product_line_edit.textChanged.connect(self.search_food)
        self.day_line_edit.textChanged.connect(self.search_day)

    def click(self):
        self.clicked = True

        self.product = self.product_combo_box.currentText()
        self.amount = self.amount_spin_box.value()
        self.day = self.day_combo_box.currentText()

        self.close()

    def search_food(self):
        with open('./source/list of food.csv', encoding='utf8') as file:
            reader = map(lambda x: x[0], list(csv.reader(file, delimiter=','))[1:])
            tag = self.product_line_edit.text().lower()

            self.product_combo_box.clear()
            self.product_combo_box.addItems(list(filter(lambda x: tag in x.lower(), reader)))

    def search_day(self):
        self.day_combo_box.clear()
        dates = map(lambda x: x[0], self.con.cursor().execute(
            f'SELECT date FROM dates WHERE date LIKE "%{self.day_line_edit.text()}%"').fetchall())
        self.day_combo_box.addItems(dates)


class EditCharacteristicsDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('./source/edit physical characteristics dialog.ui', self)

        self.clicked = False
        self.edit_btn.clicked.connect(self.click)

    def click(self):
        self.clicked = True

        coeff = {'Низкий': 1.25, 'Умеренный': 1.5, 'Интенсивный': 1.75}[self.physical_activity_level.currentText()]
        if self.sex.currentText() == 'Мужской':
            self.calorie = (10 * self.weight.value() + 6.25 * self.growth.value() + 5 * self.age.value() + 5) * coeff
        elif self.sex.currentText() == 'Женский':
            self.calorie = (10 * self.weight.value() + 6.25 * self.growth.value() + 5 * self.age.value() - 161) * coeff
        self.protein = self.weight.value() * 2
        self.fat = self.calorie * 0.25
        self.carbohydrate = self.calorie * 0.45

        self.close()


class ExitDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('./source/exit dialog.ui', self)
        self.no_clicked = True

        self.yes_btn.clicked.connect(self.yes)
        self.no_btn.clicked.connect(self.no)

    def yes(self):
        self.no_clicked = False
        self.close()

    def no(self):
        self.close()


app = QApplication(sys.argv)
ex = CalorieCounter()
ex.show()
sys.exit(app.exec())
