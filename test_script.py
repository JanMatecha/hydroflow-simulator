def main():
    print("Spouštím testovací skript...")
    result = 2 + 2
    print(f"Výsledek 2 + 2 = {result}")
    assert result == 4, "Matematika nefunguje!"
    print("Testovací skript byl úspěšně dokončen.")


if __name__ == "__main__":
    main()
