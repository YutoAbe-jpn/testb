def double(x: int) -> int:
    """与えられた整数を2倍にする"""
    return x * 2


def test_double_ok() -> None:
    """double関数が正しく動作することを確認する正常系のテスト"""
    assert 2 == double(1)


# 失敗するテストが適切に検知されるかを確認する
def test_double_ng() -> None:
    """わざと失敗するテスト"""
    assert 2 == double(2)
