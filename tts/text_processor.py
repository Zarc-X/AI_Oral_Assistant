"""
文本预处理模块
负责文本正则化、分句等预处理操作
"""
import re
from typing import List, Generator
from .config import TTS_CONFIG


class TextProcessor:
    """文本预处理器，处理TTS输入文本"""
    
    def __init__(self):
        self.sentence_delimiters = TTS_CONFIG["sentence_delimiters"]
        self.max_sentence_length = TTS_CONFIG["max_sentence_length"]
        
        # 数字转文字映射
        self.number_words = {
            '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
            '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine',
            '10': 'ten', '11': 'eleven', '12': 'twelve', '13': 'thirteen',
            '14': 'fourteen', '15': 'fifteen', '16': 'sixteen', '17': 'seventeen',
            '18': 'eighteen', '19': 'nineteen', '20': 'twenty',
            '30': 'thirty', '40': 'forty', '50': 'fifty', '60': 'sixty',
            '70': 'seventy', '80': 'eighty', '90': 'ninety'
        }
        
        # 常见缩写展开
        self.abbreviations = {
            "Mr.": "Mister",
            "Mrs.": "Misses",
            "Dr.": "Doctor",
            "Prof.": "Professor",
            "Jr.": "Junior",
            "Sr.": "Senior",
            "vs.": "versus",
            "etc.": "et cetera",
            "e.g.": "for example",
            "i.e.": "that is",
            "Jan.": "January",
            "Feb.": "February",
            "Mar.": "March",
            "Apr.": "April",
            "Aug.": "August",
            "Sept.": "September",
            "Oct.": "October",
            "Nov.": "November",
            "Dec.": "December",
        }
    
    def normalize_text(self, text: str) -> str:
        """
        文本正则化处理
        
        Args:
            text: 原始文本
            
        Returns:
            正则化后的文本
        """
        if not text:
            return ""
        
        # 去除多余空白
        text = " ".join(text.split())
        
        # 展开缩写
        text = self._expand_abbreviations(text)
        
        # 处理数字
        text = self._convert_numbers(text)
        
        # 处理货币符号
        text = self._convert_currency(text)
        
        # 处理特殊字符
        text = self._clean_special_chars(text)
        
        return text.strip()
    
    def _expand_abbreviations(self, text: str) -> str:
        """展开缩写"""
        for abbr, full in self.abbreviations.items():
            text = text.replace(abbr, full)
        return text
    
    def _convert_numbers(self, text: str) -> str:
        """将数字转换为英文单词"""
        def num_to_words(num: int) -> str:
            if num < 0:
                return "minus " + num_to_words(-num)
            if num < 21:
                return self.number_words.get(str(num), str(num))
            if num < 100:
                tens, ones = divmod(num, 10)
                if ones == 0:
                    return self.number_words.get(str(num), str(num))
                return self.number_words.get(str(tens * 10), str(tens * 10)) + " " + self.number_words.get(str(ones), str(ones))
            if num < 1000:
                hundreds, remainder = divmod(num, 100)
                result = self.number_words.get(str(hundreds), str(hundreds)) + " hundred"
                if remainder:
                    result += " and " + num_to_words(remainder)
                return result
            if num < 1000000:
                thousands, remainder = divmod(num, 1000)
                result = num_to_words(thousands) + " thousand"
                if remainder:
                    result += " " + num_to_words(remainder)
                return result
            return str(num)
        
        # 匹配独立数字
        def replace_number(match):
            try:
                num = int(match.group())
                if num < 10000000:
                    return num_to_words(num)
            except ValueError:
                pass
            return match.group()
        
        text = re.sub(r'\b\d+\b', replace_number, text)
        return text
    
    def _convert_currency(self, text: str) -> str:
        """转换货币表示"""
        # $10 -> ten dollars
        def replace_dollar(match):
            amount = match.group(1)
            try:
                num = int(amount)
                word = self._convert_numbers(str(num))
                if '.' in match.group(0):
                    return word
                return word + (" dollar" if num == 1 else " dollars")
            except (ValueError, TypeError):
                return match.group(0)
        
        text = re.sub(r'\$(\d+)', replace_dollar, text)
        return text
    
    def _clean_special_chars(self, text: str) -> str:
        """清理特殊字符"""
        # 保留基本标点和字母数字
        text = re.sub(r'[#@&*^~`|\\<>{}[\]]', '', text)
        # 多个标点合并
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        return text
    
    def split_sentences(self, text: str) -> List[str]:
        """
        将文本分割成句子
        
        Args:
            text: 输入文本
            
        Returns:
            句子列表
        """
        if not text:
            return []
        
        # 先进行正则化
        text = self.normalize_text(text)
        
        # 使用正则表达式分句
        pattern = r'(?<=[.!?;])\s+'
        sentences = re.split(pattern, text)
        
        # 处理过长的句子
        result = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if len(sentence) > self.max_sentence_length:
                # 按逗号或空格进一步分割
                sub_sentences = self._split_long_sentence(sentence)
                result.extend(sub_sentences)
            else:
                result.append(sentence)
        
        return result
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """分割过长的句子"""
        if len(sentence) <= self.max_sentence_length:
            return [sentence]
        
        # 优先按逗号分割
        parts = sentence.split(',')
        if len(parts) > 1:
            result = []
            current = ""
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if len(current) + len(part) + 2 <= self.max_sentence_length:
                    current = current + ", " + part if current else part
                else:
                    if current:
                        result.append(current)
                    current = part
            if current:
                result.append(current)
            return result
        
        # 按空格分割
        words = sentence.split()
        result = []
        current = ""
        for word in words:
            if len(current) + len(word) + 1 <= self.max_sentence_length:
                current = current + " " + word if current else word
            else:
                if current:
                    result.append(current)
                current = word
        if current:
            result.append(current)
        
        return result
    
    def stream_sentences(self, text: str) -> Generator[str, None, None]:
        """
        流式生成句子
        
        Args:
            text: 输入文本
            
        Yields:
            处理后的句子
        """
        for sentence in self.split_sentences(text):
            yield sentence


def test_processor():
    """测试文本处理器"""
    processor = TextProcessor()
    
    test_cases = [
        "Hello, how are you today?",
        "I have $10 and 20 apples.",
        "Mr. Smith went to Dr. Johnson's office.",
        "This is a very long sentence that should be split into multiple parts because it exceeds the maximum allowed length for a single TTS synthesis operation.",
        "",
        "Special chars: #@!&* should be cleaned.",
    ]
    
    print("=== 文本预处理测试 ===\n")
    for text in test_cases:
        print(f"原文: {text}")
        normalized = processor.normalize_text(text)
        print(f"正则化: {normalized}")
        sentences = processor.split_sentences(text)
        print(f"分句: {sentences}")
        print("-" * 50)


if __name__ == "__main__":
    test_processor()
