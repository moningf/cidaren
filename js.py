import json

# 你的那段数据
data = {'task_id': 155057475, 'task_type': 1, 'topic_mode': 11, 'stem': {'content': 'After  the  war,  a  convention  was  set  up  to  {frame}  a  constitution.', 'remark': '战后，为制定宪法召开了一次大会。', 'ph_us_url': None, 'ph_en_url': None, 'au_addr': None}, 'options': [{'content': 'n. 支架；骨架；框架', 'remark': None, 'answer': None, 'answer_tag': 0, 'check_code': None, 'sub_options': None, 'ph_info': None}, {'content': 'vt. 制定，拟定，创设', 'remark': None, 'answer': None, 'answer_tag': 1, 'check_code': None, 'sub_options': None, 'ph_info': None}, {'content': 'vt. 羡慕；忌妒', 'remark': None, 'answer': None, 'answer_tag': 2, 'check_code': None, 'sub_options': None, 'ph_info': None}, {'content': 'vt. 强制执行；强行实施', 'remark': None, 'answer': None, 'answer_tag': 3, 'check_code': None, 'sub_options': None, 'ph_info': None}], 'sound_mark': '', 'ph_en': '', 'ph_us': '', 'answer_num': 1, 'chance_num': 1, 'topic_done_num': 31, 'topic_total': 215, 'w_lens': [], 'w_len': 0, 'w_tip': '', 'tips': '给句中划线单词选择恰当的中文释义', 'word_type': 1, 'enable_i': 2, 'enable_i_i': 2, 'enable_i_o': 2, 'topic_code': 'lFh5eYlnlNiTVlyHeHuLbJevZJeVbVliWpyrl6LKhmJlko9ram6Wb2KRZZJfkL+NZVyWYWdub25waGiWa25vaG5lkZKRl2dgk5RuYHCYb2prZ2pfZo6SaWWVam1rb21lZGuSaXBqcWtxYmiamG1pmpdlZJQ=', 'answer_state': 1, 'show_card_type': 1}

# 转换为标准 JSON 字符串
print(json.dumps(data, ensure_ascii=False))
