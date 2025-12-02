import pickle
import hashlib
import getpass


# ==================== ĐĂNG NHẬP ====================
class AuthManager:
    def __init__(self):
        # Mật khẩu được hash bằng SHA256
        self.users = {
            'admin': self._hash_password('Admin@123')
        }
        self.max_attempts = 3
    
    def _hash_password(self, password):
        """Hash mật khẩu bằng SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def login(self):
        """Xử lý đăng nhập"""
        print("\n" + "="*50)
        print("         HỆ THỐNG QUẢN LÝ BỆNH NHÂN")
        print("              --- ĐĂNG NHẬP ---")
        print("="*50)
        
        attempts = 0
        while attempts < self.max_attempts:
            username = input("Tên đăng nhập: ")
            password = input("Mật khẩu: ")
            
            if self._verify_login(username, password):
                print(f"\n✓ Đăng nhập thành công! Xin chào, {username}!")
                return True
            else:
                attempts += 1
                remaining = self.max_attempts - attempts
                if remaining > 0:
                    print(f"✗ Sai tên đăng nhập hoặc mật khẩu! Còn {remaining} lần thử.")
                else:
                    print("✗ Đã hết số lần thử. Chương trình kết thúc.")
        
        return False
    
    def _verify_login(self, username, password):
        """Xác thực đăng nhập"""
        if username in self.users:
            return self.users[username] == self._hash_password(password)
        return False


class Patient:
    def __init__(self, id, name, age, gender, phone, visit_date):
        self.id = id
        self.name = name
        self.age = age
        self.gender = gender
        self.phone = phone
        self.visit_date = visit_date

    def __str__(self):
        return f"{self.id}: {self.name}"
    
    def __repr__(self):
        return f"Patient({self.id})"
    
    def __lt__(self, other):
        """So sánh nhỏ hơn dựa trên id"""
        if isinstance(other, Patient):
            return self.id < other.id
        return self.id < other
    
    def __gt__(self, other):
        """So sánh lớn hơn dựa trên id"""
        if isinstance(other, Patient):
            return self.id > other.id
        return self.id > other
    
    def __eq__(self, other):
        """So sánh bằng dựa trên id"""
        if isinstance(other, Patient):
            return self.id == other.id
        return self.id == other
    
    def __le__(self, other):
        return self < other or self == other
    
    def __ge__(self, other):
        return self > other or self == other
    
    def display(self):
        """Hiển thị thông tin bệnh nhân"""
        return f"ID: {self.id} | Tên: {self.name} | Tuổi: {self.age} | Giới tính: {self.gender} | SĐT: {self.phone} | Ngày khám: {self.visit_date}"


class BTreeNode:
    def __init__(self, leaf=True):
        self.keys = []  # Lưu các đối tượng Patient
        self.children = []
        self.leaf = leaf

    def is_full(self, max_keys):
        return len(self.keys) >= max_keys


class BTree:
    def __init__(self, max_keys=5):
        self.root = BTreeNode()
        self.max_keys = max_keys
        self.t = (max_keys + 1) // 2  # Bậc tối thiểu

    # ==================== THÊM BỆNH NHÂN ====================
    def insert(self, patient):
        """Thêm bệnh nhân vào B-Tree (sử dụng patient.id để sắp xếp)"""
        # Kiểm tra xem bệnh nhân đã tồn tại chưa
        patient_id = patient.id if isinstance(patient, Patient) else patient
        existing = self.search(patient_id)
        if existing:
            return (False, f"Mã bệnh nhân {patient_id} đã tồn tại! (Tên: {existing.name})")
        
        root = self.root
        
        # Nếu root đầy, cần split
        if root.is_full(self.max_keys):
            new_root = BTreeNode(leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        
        self._insert_non_full(self.root, patient)
        return (True, "Thêm thành công")

    def _insert_non_full(self, node, value):
        """Thêm key vào node chưa đầy"""
        i = len(node.keys) - 1
        
        if node.leaf:
            # Thêm vào node lá
            node.keys.append(None)
            while i >= 0 and value < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = value
        else:
            # Tìm child phù hợp
            while i >= 0 and value < node.keys[i]:
                i -= 1
            i += 1
            
            # Nếu child đầy, split nó
            if node.children[i].is_full(self.max_keys):
                self._split_child(node, i)
                if value > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.children[i], value)

    def _split_child(self, parent, index):
        """Split child thứ index của parent"""
        child = parent.children[index]
        mid_point = len(child.keys) // 2
        
        # Tạo node mới
        new_node = BTreeNode(leaf=child.leaf)
        
        # Key ở giữa sẽ được đẩy lên parent
        mid_key = child.keys[mid_point]
        
        # Copy các keys sau mid sang new_node
        new_node.keys = child.keys[mid_point + 1:]
        
        # Giữ lại các keys trước mid ở child
        child.keys = child.keys[:mid_point]
        
        # Nếu không phải leaf, copy children tương ứng
        if not child.leaf:
            new_node.children = child.children[mid_point + 1:]
            child.children = child.children[:mid_point + 1]
        
        # Chèn new_node vào parent
        parent.children.insert(index + 1, new_node)
        
        # Chèn mid_key vào parent
        parent.keys.insert(index, mid_key)

    # ==================== TÌM KIẾM BỆNH NHÂN ====================
    def search(self, patient_id, node=None):
        """Tìm kiếm bệnh nhân theo ID, trả về đối tượng Patient nếu tìm thấy"""
        if node is None:
            node = self.root
        
        for i, key in enumerate(node.keys):
            if patient_id == key:  # So sánh với patient.id
                return key  # Trả về đối tượng Patient
            if patient_id < key:
                if node.leaf:
                    return None
                return self.search(patient_id, node.children[i])
        
        if node.leaf:
            return None
        return self.search(patient_id, node.children[-1])

    # ==================== XÓA BỆNH NHÂN ====================
    def delete(self, patient_id):
        """Xóa bệnh nhân theo ID"""
        if not self.search(patient_id):
            return False
        
        self._delete(self.root, patient_id)
        
        # Nếu root rỗng và có con, thì con trở thành root mới
        if len(self.root.keys) == 0 and not self.root.leaf:
            self.root = self.root.children[0]
        
        return True
    
    def _delete(self, node, value):
        t = self.t
        
        # Tìm vị trí của key
        i = 0
        while i < len(node.keys) and value > node.keys[i]:
            i += 1
        
        # Trường hợp 1: Key nằm trong node này
        if i < len(node.keys) and value == node.keys[i]:
            if node.leaf:
                # Node là lá, xóa trực tiếp
                node.keys.pop(i)
            else:
                # Node là nút trong
                if len(node.children[i].keys) >= t:
                    # Lấy predecessor
                    predecessor = self._get_predecessor(node, i)
                    node.keys[i] = predecessor
                    self._delete(node.children[i], predecessor.id if isinstance(predecessor, Patient) else predecessor)
                elif len(node.children[i + 1].keys) >= t:
                    # Lấy successor
                    successor = self._get_successor(node, i)
                    node.keys[i] = successor
                    self._delete(node.children[i + 1], successor.id if isinstance(successor, Patient) else successor)
                else:
                    # Merge hai con
                    self._merge(node, i)
                    self._delete(node.children[i], value)
        else:
            # Key không nằm trong node này
            if node.leaf:
                return
            
            # Kiểm tra xem con có đủ key không
            if len(node.children[i].keys) < t:
                self._fill(node, i)
            
            if i > len(node.keys):
                self._delete(node.children[i - 1], value)
            else:
                self._delete(node.children[i], value)
    
    def _get_predecessor(self, node, index):
        current = node.children[index]
        while not current.leaf:
            current = current.children[-1]
        return current.keys[-1]
    
    def _get_successor(self, node, index):
        current = node.children[index + 1]
        while not current.leaf:
            current = current.children[0]
        return current.keys[0]
    
    def _fill(self, node, index):
        t = self.t
        if index > 0 and len(node.children[index - 1].keys) >= t:
            self._borrow_from_prev(node, index)
        elif index < len(node.children) - 1 and len(node.children[index + 1].keys) >= t:
            self._borrow_from_next(node, index)
        else:
            if index < len(node.keys):
                self._merge(node, index)
            else:
                self._merge(node, index - 1)
    
    def _borrow_from_prev(self, node, index):
        child = node.children[index]
        sibling = node.children[index - 1]
        child.keys.insert(0, node.keys[index - 1])
        node.keys[index - 1] = sibling.keys.pop()
        if not sibling.leaf:
            child.children.insert(0, sibling.children.pop())
    
    def _borrow_from_next(self, node, index):
        child = node.children[index]
        sibling = node.children[index + 1]
        child.keys.append(node.keys[index])
        node.keys[index] = sibling.keys.pop(0)
        if not sibling.leaf:
            child.children.append(sibling.children.pop(0))
    
    def _merge(self, node, index):
        child = node.children[index]
        sibling = node.children[index + 1]
        child.keys.append(node.keys.pop(index))
        child.keys.extend(sibling.keys)
        if not child.leaf:
            child.children.extend(sibling.children)
        node.children.pop(index + 1)

    # ==================== HIỂN THỊ CẤU TRÚC B-TREE ====================
    def get_tree_height(self, node=None):
        if node is None:
            node = self.root
        if node.leaf:
            return 1
        return 1 + self.get_tree_height(node.children[0])
    
    def get_nodes_at_level(self, target_level, node=None, current_level=0, result=None):
        if result is None:
            result = []
        if node is None:
            node = self.root
        
        if current_level == target_level:
            result.append(node)
        elif not node.leaf:
            for child in node.children:
                self.get_nodes_at_level(target_level, child, current_level + 1, result)
        
        return result

    def display(self):
        """Hiển thị cấu trúc B-Tree theo từng level"""
        print("\n" + "="*70)
        print(f"CẤU TRÚC B-TREE (max_keys = {self.max_keys})")
        print("="*70)
        
        if not self.root.keys:
            print("Cây rỗng!")
            return
        
        height = self.get_tree_height()
        total_nodes = 0
        
        for level in range(height):
            nodes = self.get_nodes_at_level(level)
            total_nodes += len(nodes)
            
            nodes_str = []
            for node in nodes:
                keys_str = [str(k.id) if isinstance(k, Patient) else str(k) for k in node.keys]
                nodes_str.append(f"[{', '.join(keys_str)}]")
            
            if level == 0:
                print(f"\n  Level {level} (Root): {' '.join(nodes_str)}")
            else:
                print(f"  Level {level}:        {' '.join(nodes_str)}")
        
        print("\n" + "-"*70)
        print(f"  Chiều cao cây: {height}")
        print(f"  Tổng số node: {total_nodes}")
        print(f"  Tổng số bệnh nhân: {self.count()}")
        print("="*70)

    def display_visual(self):
        """Hiển thị cấu trúc B-Tree dạng trực quan"""
        print("\n" + "="*70)
        print(f"CẤU TRÚC B-TREE VISUAL (max_keys = {self.max_keys})")
        print("="*70)
        
        if not self.root.keys:
            print("Cây rỗng!")
            return
        
        height = self.get_tree_height()
        
        for level in range(height):
            nodes = self.get_nodes_at_level(level)
            indent = "    " * level
            
            for i, node in enumerate(nodes):
                keys_str = [str(k.id) if isinstance(k, Patient) else str(k) for k in node.keys]
                node_type = "(Root)" if level == 0 else "(Leaf)" if node.leaf else "(Internal)"
                
                if level == 0:
                    print(f"  ┌{'─'*50}┐")
                    print(f"  │  Level 0: [{', '.join(keys_str)}] {node_type}")
                    print(f"  └{'─'*50}┘")
                else:
                    prefix = "├──" if i < len(nodes) - 1 else "└──"
                    print(f"  {indent}{prefix} [{', '.join(keys_str)}] {node_type}")
        
        print("="*70)

    # ==================== DUYỆT CÂY ====================
    def in_order_traversal(self, node=None, result=None):
        """Duyệt cây theo thứ tự tăng dần của patient.id"""
        if result is None:
            result = []
        if node is None:
            node = self.root
        
        for i, key in enumerate(node.keys):
            if not node.leaf:
                self.in_order_traversal(node.children[i], result)
            result.append(key)
        
        if not node.leaf:
            self.in_order_traversal(node.children[-1], result)
        
        return result
    
    def count(self):
        """Đếm số lượng bệnh nhân trong cây"""
        return len(self.in_order_traversal())


# ==================== QUẢN LÝ FILE NHỊ PHÂN ====================
def save_to_binary(patients, filename='patients.pat'):
    """Lưu danh sách bệnh nhân vào file nhị phân .pat"""
    try:
        with open(filename, 'wb') as file:
            pickle.dump(patients, file)
        print(f"✓ Đã lưu {len(patients)} bệnh nhân vào file nhị phân '{filename}'")
        return True
    except Exception as e:
        print(f"✗ Lỗi khi lưu file: {e}")
        return False


def load_from_binary(filename='patients.pat'):
    """Đọc danh sách bệnh nhân từ file nhị phân .pat"""
    patients = []
    try:
        with open(filename, 'rb') as file:
            patients = pickle.load(file)
        print(f"✓ Đã đọc {len(patients)} bệnh nhân từ file nhị phân '{filename}'")
    except FileNotFoundError:
        print(f"✗ File '{filename}' không tồn tại! Sẽ tạo file mới khi lưu.")
    except Exception as e:
        print(f"✗ Lỗi khi đọc file: {e}")
    return patients


# ==================== QUẢN LÝ HỒ SƠ BỆNH NHÂN ====================
class PatientManager:
    def __init__(self, filename='patients.pat', max_keys=5):
        self.filename = filename
        self.btree = BTree(max_keys=max_keys)
        self.next_id = 1  # ID tự động tăng
        self.load_from_file()
    
    def load_from_file(self):
        """Đọc dữ liệu từ file nhị phân và thêm vào B-Tree"""
        patients = load_from_binary(self.filename)
        max_id = 0
        for patient in patients:
            self.btree.insert(patient)
            if patient.id > max_id:
                max_id = patient.id
        # Cập nhật next_id = max_id + 1
        self.next_id = max_id + 1
    
    def get_next_id(self):
        """Lấy ID tiếp theo và tự động tăng"""
        current_id = self.next_id
        self.next_id += 1
        return current_id
    
    def save_to_file(self):
        """Lưu tất cả bệnh nhân từ B-Tree vào file nhị phân"""
        patients = self.btree.in_order_traversal()
        save_to_binary(patients, self.filename)
    
    def add_patient(self):
        """Thêm bệnh nhân mới"""
        print("\n" + "-"*40)
        print("THÊM BỆNH NHÂN MỚI")
        print("-"*40)
        
        try:
            # ID tự động tăng
            id = self.get_next_id()
            print(f"Mã bệnh nhân (ID): {id} (tự động)")
            
            name = input("Nhập họ tên bệnh nhân: ")
            age = int(input("Nhập tuổi: "))
            gender = input("Nhập giới tính (Nam/Nu): ")
            phone = input("Nhập số điện thoại: ")
            visit_date = input("Nhập ngày khám (YYYY-MM-DD): ")
            
            patient = Patient(id, name, age, gender, phone, visit_date)
            success, message = self.btree.insert(patient)
            
            if success:
                self.save_to_file()
                print(f"✓ Đã thêm bệnh nhân thành công!")
                print(f"  {patient.display()}")
            else:
                print(f"✗ Thêm bệnh nhân thất bại! {message}")
                # Giảm lại ID nếu thêm thất bại
                self.next_id -= 1
            
        except ValueError:
            print("✗ Dữ liệu không hợp lệ!")
            # Giảm lại ID nếu có lỗi
            self.next_id -= 1
    
    def search_patient(self):
        """Tìm kiếm bệnh nhân theo ID"""
        print("\n" + "-"*40)
        print("TÌM KIẾM BỆNH NHÂN")
        print("-"*40)
        
        try:
            id = int(input("Nhập mã bệnh nhân cần tìm: "))
            patient = self.btree.search(id)
            
            if patient:
                print(f"✓ Tìm thấy bệnh nhân:")
                print(f"  {patient.display()}")
            else:
                print(f"✗ Không tìm thấy bệnh nhân với ID = {id}")
                
        except ValueError:
            print("✗ Mã bệnh nhân không hợp lệ!")
    
    def delete_patient(self):
        """Xóa bệnh nhân theo ID"""
        print("\n" + "-"*40)
        print("XÓA BỆNH NHÂN")
        print("-"*40)
        
        try:
            id = int(input("Nhập mã bệnh nhân cần xóa: "))
            patient = self.btree.search(id)
            
            if patient:
                print(f"  Thông tin: {patient.display()}")
                confirm = input(f"Bạn có chắc muốn xóa bệnh nhân này? (y/n): ")
                if confirm.lower() == 'y':
                    self.btree.delete(id)
                    self.save_to_file()
                    print(f"✓ Đã xóa bệnh nhân ID = {id}")
                else:
                    print("✗ Hủy xóa")
            else:
                print(f"✗ Không tìm thấy bệnh nhân với ID = {id}")
                
        except ValueError:
            print("✗ Mã bệnh nhân không hợp lệ!")
    
    def display_tree(self):
        """Hiển thị cấu trúc B-Tree"""
        self.btree.display()
        self.btree.display_visual()
    
    def display_all_patients(self):
        """Hiển thị danh sách tất cả bệnh nhân"""
        print("\n" + "="*90)
        print("DANH SÁCH TẤT CẢ BỆNH NHÂN (Sắp xếp theo ID)")
        print("="*90)
        
        patients = self.btree.in_order_traversal()
        if not patients:
            print("Chưa có bệnh nhân nào trong hệ thống.")
            return
        
        print(f"{'ID':<6} {'Họ tên':<25} {'Tuổi':<6} {'Giới tính':<10} {'SĐT':<15} {'Ngày khám':<12}")
        print("-"*90)
        
        for p in patients:
            print(f"{p.id:<6} {p.name:<25} {p.age:<6} {p.gender:<10} {p.phone:<15} {p.visit_date:<12}")
        
        print("-"*90)
        print(f"Tổng số: {len(patients)} bệnh nhân")


def main_menu():
    """Menu chính"""
    # Đăng nhập trước
    auth = AuthManager()
    if not auth.login():
        return
    
    print("\n" + "="*50)
    print("     HỆ THỐNG QUẢN LÝ HỒ SƠ BỆNH NHÂN")
    print("         (Sử dụng B-Tree & File Nhị Phân)")
    print("="*50)
    
    manager = PatientManager(filename='patients.pat', max_keys=5)
    
    while True:
        print("\n" + "="*50)
        print("                    MENU")
        print("="*50)
        print("1. Thêm bệnh nhân mới")
        print("2. Tìm kiếm bệnh nhân theo ID")
        print("3. Xóa bệnh nhân theo ID")
        print("4. Hiển thị cấu trúc B-Tree")
        print("5. Hiển thị danh sách bệnh nhân")
        print("6. Lưu dữ liệu vào file")
        print("0. Thoát")
        print("-"*50)
        
        choice = input("Chọn chức năng (0-6): ")
        
        if choice == '1':
            manager.add_patient()
        elif choice == '2':
            manager.search_patient()
        elif choice == '3':
            manager.delete_patient()
        elif choice == '4':
            manager.display_tree()
        elif choice == '5':
            manager.display_all_patients()
        elif choice == '6':
            manager.save_to_file()
        elif choice == '0':
            print("\nTạm biệt!")
            break
        else:
            print("✗ Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    main_menu()
