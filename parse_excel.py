#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import zipfile
import os
import sys
from datetime import datetime

def parse_shared_strings(shared_strings_content):
    """解析sharedStrings.xml文件，返回字符串列表"""
    try:
        root = ET.fromstring(shared_strings_content)
        strings = []
        for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si'):
            # 提取文本内容，可能包含多个r标签
            text_parts = []
            for t in si.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                if t.text:
                    text_parts.append(t.text)
            text = ''.join(text_parts).strip()
            strings.append(text)
        return strings
    except Exception as e:
        print(f"解析sharedStrings.xml时出错: {e}")
        return []

def parse_sheet_data(sheet_content, shared_strings):
    """解析sheet1.xml文件，提取学生数据"""
    try:
        root = ET.fromstring(sheet_content)
        students = []
        
        # 查找所有行
        for row in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
            row_num = int(row.get('r'))
            if row_num == 1:
                continue  # 跳过标题行
            
            cells = {}
            for cell in row.findall('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                cell_ref = cell.get('r')  # 如A1, B1等
                cell_type = cell.get('t')
                value_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                
                if value_elem is not None and value_elem.text:
                    value = value_elem.text
                    if cell_type == 's':  # 字符串类型
                        try:
                            idx = int(value)
                            if idx < len(shared_strings):
                                cells[cell_ref] = shared_strings[idx]
                            else:
                                cells[cell_ref] = value
                        except ValueError:
                            cells[cell_ref] = value
                    else:
                        cells[cell_ref] = value
            
            # 根据已知结构解析学生信息
            # 从sharedStrings.xml看出列结构：A=序号, B=高中, C=称呼, D=姓, E=名, F=邮箱, G=?, H=?, I=出生日期Excel值
            student = {
                '序号': cells.get('A{}'.format(row_num), ''),
                '高中': cells.get('B{}'.format(row_num), ''),
                '称呼': cells.get('C{}'.format(row_num), ''),
                '姓': cells.get('D{}'.format(row_num), ''),
                '名': cells.get('E{}'.format(row_num), ''),
                '邮箱': cells.get('F{}'.format(row_num), ''),
                '出生日期_excel': cells.get('I{}'.format(row_num), '')
            }
            
            # 计算年龄（如果出生日期可用）
            if student['出生日期_excel']:
                try:
                    # Excel日期：1900年1月1日为1，需要转换
                    excel_date = float(student['出生日期_excel'])
                    if excel_date > 60:
                        excel_date -= 1  # Excel的1900年闰年错误修正
                    
                    base_date = datetime(1899, 12, 30)
                    birth_date = base_date + timedelta(days=excel_date)
                    
                    # 计算年龄（以2026年为基准）
                    age = 2026 - birth_date.year
                    student['年龄'] = str(age)
                    student['出生日期'] = birth_date.strftime('%Y-%m-%d')
                except:
                    student['年龄'] = ''
                    student['出生日期'] = ''
            
            # 组合完整姓名
            if student['姓'] or student['名']:
                student['姓名'] = f"{student['姓']}{student['名']}".strip()
            else:
                student['姓名'] = ''
            
            students.append(student)
        
        return students
    except Exception as e:
        print(f"解析sheet数据时出错: {e}")
        return []

def extract_excel_data(excel_path):
    """从Excel文件中提取数据"""
    try:
        with zipfile.ZipFile(excel_path, 'r') as z:
            # 读取sharedStrings.xml
            shared_strings_content = z.read('xl/sharedStrings.xml')
            shared_strings = parse_shared_strings(shared_strings_content)
            
            # 读取sheet1.xml
            sheet_content = z.read('xl/worksheets/sheet1.xml')
            students = parse_sheet_data(sheet_content, shared_strings)
            
            return students
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return []

def main():
    # 测试解析Esigelec学生文件
    excel_path = "/Users/yangyan/Downloads/同步空间/HelenOA/Esigelec/liste d'étudiant 2023.xlsx"
    if os.path.exists(excel_path):
        print(f"正在解析文件: {excel_path}")
        students = extract_excel_data(excel_path)
        
        print(f"找到 {len(students)} 名学生")
        for i, student in enumerate(students[:10], 1):  # 只显示前10名
            print(f"{i}. 姓名: {student.get('姓名', 'N/A')}, "
                  f"高中: {student.get('高中', 'N/A')}, "
                  f"年龄: {student.get('年龄', 'N/A')}, "
                  f"邮箱: {student.get('邮箱', 'N/A')}")
    else:
        print(f"文件不存在: {excel_path}")

if __name__ == "__main__":
    from datetime import timedelta
    main()