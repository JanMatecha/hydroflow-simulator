from test_script import main


def test_main(capsys):
    main()

    output = capsys.readouterr().out
    assert "Výsledek 2 + 2 = 4" in output
    assert "Testovací skript byl úspěšně dokončen." in output
