class Data:
    test = "abe"

    def __init__(self) -> None:
        self.nums = [1, 2, 3, 4, 5]

    def change_data(self, index, n) -> None:
        self.nums[index] = n


data = Data()
data.change_data(0, 100)
data.test = "hoge"
print(data.nums)
print(data.test)
data2 = Data()
print(data2.test)
Data.test = "yuto"
print(data2.test)
print(data.test)
