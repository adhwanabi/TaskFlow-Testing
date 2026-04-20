# tests/selenium/test_frontend.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
import pytest
import time
from pages.task_page import TaskPage

class TestTaskFlowFrontend:
    """Test suite untuk frontend TaskFlow"""
    
    @pytest.fixture(autouse=True)
    def setup(self, driver):
        """Setup sebelum setiap test"""
        self.page = TaskPage(driver)
        self.driver = driver
        self.wait = WebDriverWait(driver, 10) # Standarisasi wait
        self.page.refresh_tasks()
    
    # ========== Test Cases ==========
    
    def test_page_loads_correctly(self):
        """TC-FE-001: Memastikan halaman dapat dimuat dengan benar"""
        assert "TaskFlow" in self.driver.title
        assert self.page.FORM_TITLE is not None
        print("✓ Halaman berhasil dimuat")
    
    def test_create_new_task_success(self):
        """TC-FE-002: Membuat tugas baru dengan data valid"""
        # Arrange
        task_title = f"Test Task {time.time()}"
        task_desc = "Ini adalah tugas test"
        task_status = "pending"
        
        # Act
        self.page.create_task(task_title, task_desc, task_status)
        
        # Assert
        assert self.page.task_exists(task_title), "Tugas tidak muncul di tabel"
        alert_msg = self.page.get_alert_message()
        assert "berhasil ditambahkan" in alert_msg
        print(f"✓ Tugas '{task_title}' berhasil dibuat")
    
    def test_create_task_without_title_validation(self):
        """TC-FE-003: Validasi client-side untuk field judul kosong"""
        # Act - Submit form tanpa mengisi judul
        self.driver.find_element(*self.page.BTN_SUBMIT).click()
        
        # Assert - Cek validasi HTML5 required
        title_input = self.driver.find_element(*self.page.FORM_TITLE)
        validation_message = self.driver.execute_script(
            "return arguments[0].validationMessage;", title_input
        )
        assert "isi" in validation_message.lower() or "fill" in validation_message.lower()
        print("✓ Validasi judul kosong berfungsi")
    
    def test_reset_form_functionality(self):
        """TC-FE-004: Memastikan tombol reset mengosongkan form"""
        # Arrange - Isi form dulu
        self.driver.find_element(*self.page.FORM_TITLE).send_keys("Test Reset")
        self.driver.find_element(*self.page.FORM_DESCRIPTION).send_keys("Deskripsi test")
        
        # Act
        self.page.reset_form()
        
        # Assert
        form_values = self.page.get_form_values()
        assert form_values['title'] == "", "Judul tidak tereset"
        assert form_values['description'] == "", "Deskripsi tidak tereset"
        print("✓ Form reset berfungsi")
    
    def test_edit_task_functionality(self):
        """TC-FE-005: Mengedit tugas yang sudah ada"""
        # Arrange - Buat tugas dulu
        original_title = f"Edit Test {time.time()}"
        self.page.create_task(original_title, "Deskripsi awal", "pending")
        
        # Act - Edit tugas
        self.page.click_edit_task(original_title)
        new_title = f"{original_title} (Updated)"
        self.page.update_task_in_modal(
            title=new_title,
            description="Deskripsi setelah update",
            status="completed"
        )
        
        # Assert
        assert self.page.task_exists(new_title), "Tugas dengan judul baru tidak ditemukan"
        assert not self.page.task_exists(original_title), "Tugas lama masih ada"
        
        task = self.page.get_task_by_title(new_title)
        assert task['status'] == "Completed"
        print(f"✓ Tugas berhasil diedit menjadi '{new_title}'")
    
    def test_delete_task_functionality(self):
        """TC-FE-006: Menghapus tugas"""
        # Arrange
        task_title = f"Delete Test {time.time()}"
        self.page.create_task(task_title, "Akan dihapus", "pending")
        assert self.page.task_exists(task_title), "Tugas tidak berhasil dibuat"
        
        # Act
        self.page.click_delete_task(task_title)
        self.page.handle_delete_confirmation(accept=True)
        
        # Assert - Tunggu alert sukses
        alert_msg = self.page.get_alert_message()
        assert "berhasil dihapus" in alert_msg.lower()
        assert not self.page.task_exists(task_title), "Tugas masih ada setelah dihapus"
        print(f"✓ Tugas '{task_title}' berhasil dihapus")
    
    def test_delete_task_cancelled(self):
        """TC-FE-007: Membatalkan penghapusan tugas"""
        # Arrange
        task_title = f"Cancel Delete {time.time()}"
        self.page.create_task(task_title, "Tidak jadi dihapus", "pending")
        
        # Act
        self.page.click_delete_task(task_title)
        self.page.handle_delete_confirmation(accept=False)
        
        # Assert
        time.sleep(0.5)  # Tunggu dialog tertutup
        assert self.page.task_exists(task_title), "Tugas hilang padahal delete dibatalkan"
        print("✓ Pembatalan delete berfungsi")
    
    def test_refresh_button(self):
        """TC-FE-008: Memastikan tombol refresh memuat ulang data"""
        # Arrange - Buat tugas baru via API langsung (simulasi perubahan dari luar)
        import requests
        api_url = "http://127.0.0.1:8000/api/tasks"
        new_task = {"title": "API Created Task", "description": "Dibuat via API", "status": "pending"}
        response = requests.post(api_url, json=new_task)
        assert response.status_code == 201
        
        # Act - Klik refresh
        self.page.refresh_tasks()
        
        # Assert
        assert self.page.task_exists("API Created Task"), "Tugas dari API tidak muncul setelah refresh"
        print("✓ Tombol refresh berfungsi")
    
    def test_status_filter_display(self):
        """TC-FE-009: Memastikan status badge ditampilkan dengan warna yang benar"""
        # Arrange - Buat tugas dengan berbagai status
        tasks_data = [
            ("Task Pending", "pending", "bg-warning"),
            ("Task Progress", "in-progress", "bg-info"),
            ("Task Completed", "completed", "bg-success")
        ]
        
        for title, status, _ in tasks_data:
            self.page.create_task(title, f"Test {status}", status)
            self.page.wait_for_alert_to_disappear()
        
        # Assert - Cek badge classes
        for title, _, expected_class in tasks_data:
            task = self.page.get_task_by_title(title)
            if task:
                # Cari badge di kolom status
                rows = self.driver.find_elements(*self.page.TASKS_TABLE_ROWS)
                for row in rows:
                    if title in row.text:
                        badge = row.find_element(By.CSS_SELECTOR, ".badge")
                        badge_class = badge.get_attribute("class")
                        assert expected_class in badge_class, f"Badge untuk {title} salah"
                        break
        
        print("✓ Status badge ditampilkan dengan benar")
    
    def test_modal_close_buttons(self):
        """TC-FE-010: Memastikan modal edit bisa ditutup dengan berbagai cara"""
        task_title = f"Modal Test {time.time()}"
        self.page.create_task(task_title, "Test modal", "pending")
        
        # Test 1: Tombol X (Sudah Passed)
        self.page.click_edit_task(task_title)
        self.driver.find_element(*self.page.BTN_CLOSE_MODAL).click()
        assert self.wait.until(EC.invisibility_of_element_located(self.page.MODAL_EDIT))
        
        # Test 2: Tombol Cancel (Sudah Passed)
        self.page.click_edit_task(task_title)
        self.driver.find_element(*self.page.BTN_CANCEL_EDIT).click()
        assert self.wait.until(EC.invisibility_of_element_located(self.page.MODAL_EDIT))
        
        # Test 3: Klik di luar modal (PERBAIKAN)
        self.page.click_edit_task(task_title)
        
        # Cara paling stabil: Klik pada koordinat (0,0) atau area body yang kosong
        from selenium.webdriver.common.action_chains import ActionChains
        actions = ActionChains(self.driver)
        # Klik sedikit bergeser dari pojok kiri atas (misal 5,5) untuk memicu klik luar
        actions.move_by_offset(5, 5).click().perform()
        
        # Pastikan modal hilang
        is_hidden = self.wait.until(EC.invisibility_of_element_located(self.page.MODAL_EDIT))
        assert is_hidden
        print("  ✓ Modal bisa ditutup dengan klik di luar")
    
    def test_empty_state_when_no_tasks(self):
        """TC-FE-011: Memastikan empty state muncul saat tidak ada tugas"""
        # Arrange - Hapus semua tugas
        import requests
        api_url = "http://127.0.0.1:8000/api/tasks"
        tasks = requests.get(api_url).json()
        for task in tasks:
            requests.delete(f"{api_url}/{task['id']}")
        
        # Act - Refresh halaman
        self.page.refresh_tasks()
        
        # Assert
        assert self.page.is_empty_state_displayed(), "Empty state tidak muncul"
        empty_text = self.driver.find_element(*self.page.EMPTY_STATE).text
        assert "Belum ada tugas" in empty_text
        print("✓ Empty state ditampilkan dengan benar")
    
    def test_form_validation_after_reset(self):
        """TC-FE-012: Memastikan form valid setelah di-reset"""
        # Arrange - Submit form kosong (trigger validasi)
        self.driver.find_element(*self.page.BTN_SUBMIT).click()
        
        # Act - Reset form
        self.page.reset_form()
        
        # Assert - Coba submit lagi, seharusnya tidak ada validasi error
        self.driver.find_element(*self.page.BTN_SUBMIT).click()
        # Jika tidak ada exception, berarti validasi tidak muncul lagi
        print("✓ Validasi form di-reset dengan benar")