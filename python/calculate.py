def calculate_rate(level: float, achievement_rate: float) -> int:
    """
    レベルと達成率からレート値を計算する関数。

    Args:
        level (float): レベル (1.0〜15.0)。
        achievement_rate (float): 達成率 (0.0000〜101.0000)。

    Returns:
        int: 計算されたレート値（小数点以下切り捨て）。

    """

    achievement_rate = achievement_rate /10000

    #百分率に変換　例980000→　98.0000

    if achievement_rate >= 100.50:
        achievement_rate =100.50

    rank_coefficients = {
        100.50: 22.4,
        100.4999: 22.2,
        100.00: 21.6,
        99.99: 21.4,
        99.50: 21.1,
        99.00: 20.8,
        98.99: 20.6,
        98.00: 20.3,
        97.00: 20.0,
        96.99: 17.6,
        94.00: 16.8,
        90.00: 15.2,
        80.00: 13.6,
        79.99: 12.8,
        75.00: 12.0,
        70.00: 11.2,
        60.00: 9.6,
        50.00: 8.0,
        40.00: 6.4,
        30.00: 4.8,
        20.00: 3.2,
        10.00: 1.6,
        0.00: 0.0,
    }

    rank_coefficient = 0.0
    sorted_rates = sorted(rank_coefficients.keys(), reverse=True)

    for rate in sorted_rates:
        if achievement_rate >= rate:
            rank_coefficient = rank_coefficients[rate]
            break

    rate_value = level * (achievement_rate / 100) * rank_coefficient
    return int(rate_value)

# 関数の使用例

"""

level = 10.0
achievement = 98.50
rate = calculate_rate(level, achievement)
print(f"レベル: {level}, 達成率: {achievement} の時のレート値: {rate}")

level = 5.0
achievement = 100.80
rate = calculate_rate(level, achievement)
print(f"レベル: {level}, 達成率: {achievement} の時のレート値: {rate}")

level = 15.0
achievement = 50.00
rate = calculate_rate(level, achievement)
print(f"レベル: {level}, 達成率: {achievement} の時のレート値: {rate}")

"""

level = 13.4
achievement = 1010000
rate = calculate_rate(level, achievement)
print(f"レベル: {level}, 達成率: {achievement} の時のレート値: {rate}")