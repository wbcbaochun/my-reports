#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import zipfile
import os
import sys
import csv
from datetime import datetime, timedelta

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
            age = ''
            birth_date_str = ''
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
                    birth_date_str = birth_date.strftime('%Y-%m-%d')
                    student['出生日期'] = birth_date_str
                except:
                    student['年龄'] = ''
                    student['出生日期'] = ''
            
            # 组合完整姓名
            if student['姓'] or student['名']:
                full_name = f"{student['姓']}{student['名']}".strip()
            else:
                full_name = ''
            
            # 清理数据
            cleaned_student = {
                '姓名': full_name,
                '年龄': student.get('年龄', ''),
                '邮箱': student.get('邮箱', ''),
                '高中': student.get('高中', ''),
                '序号': student.get('序号', ''),
                '出生日期': student.get('出生日期', '')
            }
            
            if full_name:  # 只添加有姓名的学生
                students.append(cleaned_student)
        
        return students
    except Exception as e:
        print(f"解析sheet数据时出错: {e}")
        return []

def extract_excel_data(excel_path, school_name):
    """从Excel文件中提取数据，指定学校名称"""
    try:
        with zipfile.ZipFile(excel_path, 'r') as z:
            # 读取sharedStrings.xml
            shared_strings_content = z.read('xl/sharedStrings.xml')
            shared_strings = parse_shared_strings(shared_strings_content)
            
            # 读取sheet1.xml
            sheet_content = z.read('xl/worksheets/sheet1.xml')
            students = parse_sheet_data(sheet_content, shared_strings)
            
            # 为每个学生添加学校信息
            for student in students:
                student['学校'] = school_name
            
            return students
    except Exception as e:
        print(f"读取Excel文件时出错 {excel_path}: {e}")
        return []

def extract_shnu_2021_data():
    """提取上师大2021年学生数据"""
    # 从记忆文件中已知有5名学生
    students = [
        {'姓名': '熊悦', '年龄': '', '邮箱': '', '高中': '', '序号': '1', '出生日期': '', '学校': '上海师范大学 (SHNU) - Epitech项目'},
        {'姓名': '雷知雨', '年龄': '', '邮箱': '1839084624@qq.com', '高中': '', '序号': '2', '出生日期': '', '学校': '上海师范大学 (SHNU) - Epitech项目'},
        {'姓名': '江一帆', '年龄': '', '邮箱': 'Nafiy719@163.com', '高中': '', '序号': '3', '出生日期': '', '学校': '上海师范大学 (SHNU) - Epitech项目'},
        {'姓名': '卢可奇', '年龄': '', '邮箱': '463683868@qq.com', '高中': '', '序号': '4', '出生日期': '', '学校': '上海师范大学 (SHNU) - Epitech项目'},
        {'姓名': '吴恒芝', '年龄': '', '邮箱': '15990479387@163.com', '高中': '', '序号': '5', '出生日期': '', '学校': '上海师范大学 (SHNU) - Epitech项目'}
    ]
    return students

def save_to_csv(students, output_path):
    """保存学生数据到CSV文件"""
    if not students:
        print("没有学生数据可保存")
        return False
    
    try:
        # 获取所有可能的字段
        fieldnames = set()
        for student in students:
            fieldnames.update(student.keys())
        
        # 确定字段顺序
        field_order = ['学校', '姓名', '年龄', '邮箱', '高中', '序号', '出生日期']
        # 确保所有字段都在field_order中
        for field in fieldnames:
            if field not in field_order:
                field_order.append(field)
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_order)
            writer.writeheader()
            for student in students:
                writer.writerow(student)
        
        print(f"数据已保存到: {output_path}")
        print(f"总学生数: {len(students)}")
        return True
    except Exception as e:
        print(f"保存CSV文件时出错: {e}")
        return False

def main():
    all_students = []
    
    # 1. 提取Esigelec学生数据
    esigelec_path = "/Users/yangyan/Downloads/同步空间/HelenOA/Esigelec/liste d'étudiant 2023.xlsx"
    if os.path.exists(esigelec_path):
        print(f"正在解析Esigelec文件: {esigelec_path}")
        esigelec_students = extract_excel_data(esigelec_path, "ESIGELEC")
        print(f"从Esigelec找到 {len(esigelec_students)} 名学生")
        all_students.extend(esigelec_students)
    else:
        print(f"Esigelec文件不存在: {esigelec_path}")
    
    # 2. 提取上师大2021年学生数据
    print("提取上师大2021年学生数据")
    shnu_students = extract_shnu_2021_data()
    print(f"从上师大找到 {len(shnu_students)} 名学生")
    all_students.extend(shnu_students)
    
    # 3. 尝试提取Eicar学生数据
    eicar_path = "/Users/yangyan/Downloads/同步空间/HelenOA/eicar/étudiants eicar-Hélène.xlsx"
    if os.path.exists(eicar_path):
        print(f"正在解析Eicar文件: {eicar_path}")
        eicar_students = extract_excel_data(eicar_path, "EICAR")
        print(f"从Eicar找到 {len(eicar_students)} 名学生")
        all_students.extend(eicar_students)
    else:
        print(f"Eicar文件不存在: {eicar_path}")
    
    # 4. 尝试提取其他学生数据文件
    # 检查法语教学名单
    french_teaching_dir = "/Users/yangyan/Downloads/同步空间/HelenOA/法语教学/名单"
    if os.path.exists(french_teaching_dir):
        print(f"扫描法语教学目录: {french_teaching_dir}")
        for filename in os.listdir(french_teaching_dir):
            if filename.endswith(('.xls', '.xlsx')):
                file_path = os.path.join(french_teaching_dir, filename)
                print(f"  发现文件: {filename}")
                # 这里可以添加解析逻辑，但需要先了解文件结构
    
    # 保存所有学生数据
    output_csv = "/Users/yangyan/.openclaw/workspace/helenoa_students.csv"
    if save_to_csv(all_students, output_csv):
        print(f"\n汇总结果:")
        print(f"总学生数: {len(all_students)}")
        
        # 按学校统计
        school_counts = {}
        for student in all_students:
            school = student.get('学校', '未知')
            school_counts[school] = school_counts.get(school, 0) + 1
        
        print("\n按学校分布:")
        for school, count in school_counts.items():
            print(f"  {school}: {count} 名学生")
        
        print(f"\nCSV文件已保存，可以使用Excel打开: {output_csv}")
        print("建议: 使用Excel打开CSV文件，然后另存为Excel格式 (.xlsx)")
    else:
        print("保存数据失败")

if __name__ == "__main__":
    main()