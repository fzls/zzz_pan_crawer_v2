# print("%.2f"%(4/3))

# tests = [1.1, 1.4, 1.5, 1.55, 1.67, 1.9, 20.5, 4]
# for t in tests:
#     print("ori: %f  int: %d  res: %f" % (t, int(t), t - int(t)))
# import sys
#
# sys.stdout.clear()
# import time
# while True:
#     print(time.time())
#     time.sleep(0.001)
import logging
import time

PROGRESS_BAR_LENGTH = 10
# blocks
BLOCKS = [
    u'  ',  # 0/8 BLOCK
    u'\u258F',  # 1/8 BLOCK
    u'\u258E',  # 2/8 BLOCK
    u'\u258D',  # 3/8 BLOCK
    u'\u258C',  # 4/8 BLOCK
    u'\u258B',  # 5/8 BLOCK
    u'\u258A',  # 6/8 BLOCK
    u'\u2589',  # 7/8 BLOCK
    u'\u2588',  # 8/8 BLOCK
]

# FULL = 8
# EMPTY = 0
#
#
# def get_progress_bar(progress, total):
#     global PROGRESS_BAR_LENGTH, BLOCKS, FULL, EMPTY
#
#     percent = 100 * progress / total
#     total_parts = 8 * PROGRESS_BAR_LENGTH
#     parts = int(percent / 100 * total_parts)
#
#     full_block = int(parts / 8)
#     last_block = int(parts % 8)
#     empty_block = PROGRESS_BAR_LENGTH - full_block - 1
#     return ' [ ' + "%5.2f %% " % percent + str(BLOCKS[FULL] * full_block) + BLOCKS[last_block] + str(BLOCKS[
#                                                                                                          EMPTY] * empty_block) + ' ] '
#     pass
#
#
# for t in range(100 + 1):
#     sys.stdout.write('\r' + get_progress_bar(t, 100))
#     time.sleep(1)

# print("\u2588%d\u2588"%123)
# print('  \u2588  \u2588  \u2588  \u2588')
# print('\u2588  \u2588  \u2588  \u2588  ')


# set logging level
MyINFO = 45
logging.addLevelName(level=MyINFO, levelName='MyINFO')
# 记录到文件
logging.basicConfig(level=MyINFO,
                    format='%(asctime)s [line:%(lineno)d] : %(message)s',
                    datefmt='%H:%M:%S',
                    filename='tmp/_downloader_[' + time.strftime('%d_%b_%Y-%H_%M_%S') + '].log',
                    filemode='w')

logging.log(MyINFO, "test directory")
logging.log(MyINFO, "test directory2")
logging.log(MyINFO, "test directory3")
logging.log(MyINFO, "test directory4")
