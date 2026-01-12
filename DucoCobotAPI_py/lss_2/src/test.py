def min_remaining_numbers(n, m, k, nums):
# 将集合中的元素进行排序
    nums.sort()


    # 从前往后遍历集合
    i = 0
    while i <= len(nums) - m:
    # 检查这m个元素中的最大值和最小值的差是否小于等于k
        if nums[i + m - 1] - nums[i] <= k:
        # 满足条件，删除最小值，将剩余m-1个元素保留
            nums.pop(i)
        else:
        # 如果不满足条件，跳过下一个元素继续检查
            i += 1

    return len(nums)

# 输入
n, m, k = map(int, input().split())
nums = list(map(int, input().split()))

# 输出最少剩余的数字数量
print(min_remaining_numbers(n, m, k, nums))