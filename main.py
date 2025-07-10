from utils import KRS, mail, menu
import json
import time

def main():
    menu.menu()
    while True:
        user_choice = input(">> Wybierz opcję: ").strip()
        if user_choice == "1":
            KRS.create_companies_watchlist()
        elif user_choice == "2":
            n_comp = int(input("Ile spółek chcesz usunąć?"))
            for _ in range(n_comp):
                KRS.remove_from_watchlist(input("Podaj nr krs: "))
        elif user_choice == "3":
            to_mail = input("podaj adres email na jaki mają zostać wysłane zmiany: ")
            while True:
                try:
                    companies_changed = KRS.get_recent_changes()
                    my_changed_companies = KRS.check_if_changed(companies_changed)
                    if my_changed_companies:
                        changes = json.dumps(KRS.check_what_changed(my_changed_companies), ensure_ascii=False, indent=2)
                        mail.send_mail("zmiany w spółkach", changes, to_mail)
                    time.sleep(60)
                except KeyboardInterrupt:
                    break

if __name__ == "__main__":
    main()