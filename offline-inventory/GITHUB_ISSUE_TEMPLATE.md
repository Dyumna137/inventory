# GitHub Issue Template: Buttons Disappear When Changing Inventory Type

## 🐛 **Bug Report**

### **Title:** 
```
UI buttons disappear when changing inventory type in GUI
```

### **Description:**
When using the "Change Inventory Type" feature in the GUI, all buttons in the interface disappear and become inaccessible, requiring the user to restart the application.

### **Steps to Reproduce:**
1. Launch the inventory management application (`python main.py`)
2. Ensure the GUI loads with visible buttons and data
3. Go to **Tools** → **Change Inventory Type...**
4. Select a different inventory type (e.g., change from Library to Retail)
5. Click **Apply**
6. Observe that buttons disappear from the interface

### **Expected Behavior:**
- Buttons should remain visible and functional after changing inventory type
- Form fields should update to show new inventory type fields
- Table should refresh with new column headers
- All UI elements should remain accessible

### **Actual Behavior:**
- Buttons disappear from the interface
- User cannot access functionality without restarting application
- UI becomes partially unusable

### **Environment:**
- **OS:** Windows 11
- **Python Version:** 3.13
- **GUI Framework:** tkinter with ttk
- **Database:** SQLite
- **Application Version:** Latest main branch

### **Additional Context:**
- The issue occurs consistently when switching between any inventory types
- Data loading appears to work correctly (items are loaded from database)
- Only the button visibility is affected
- Application console shows successful UI refresh messages but buttons remain invisible

### **Screenshots:**
(You would add screenshots here showing before/after the issue)

### **Possible Root Cause:**
The issue likely occurs in the `refresh_ui_after_type_change()` function in `gui/gui.py` where UI components are being reconfigured. The table column reconfiguration or global variable management may be interfering with button widget visibility.

### **Code Location:**
- **File:** `gui/gui.py`
- **Function:** `refresh_ui_after_type_change()`
- **Lines:** Approximately 737-890

### **Suggested Investigation:**
1. Check if button widgets are being inadvertently destroyed or hidden during UI refresh
2. Verify that global variable references to UI components remain valid
3. Test if the issue is related to tkinter widget hierarchy changes
4. Add debugging to track button widget states during type changes

### **Priority:** 
**High** - Significantly impacts user experience and core functionality

### **Labels:**
`bug`, `gui`, `high-priority`, `user-experience`

---

## 📝 **How to Create This Issue on GitHub:**

### **Step 1: Navigate to Your Repository**
1. Go to: `https://github.com/Dyumna137/inventory`
2. Click on the **"Issues"** tab

### **Step 2: Create New Issue**
1. Click the green **"New issue"** button
2. Use the title: `UI buttons disappear when changing inventory type in GUI`

### **Step 3: Fill in the Issue**
1. Copy the description from above
2. Add any screenshots you can take showing the problem
3. Add labels: `bug`, `gui`, `high-priority`

### **Step 4: Submit**
1. Click **"Submit new issue"**
2. GitHub will assign it an issue number (e.g., #1, #2, etc.)

### **Additional Tips:**
- **Add Screenshots:** Take before/after screenshots showing buttons disappearing
- **Tag Yourself:** Assign the issue to yourself if you'll be working on it
- **Add Milestone:** If you have project milestones, add this to the appropriate one
- **Reference Code:** Use GitHub's code linking to reference specific lines

Would you like me to help you refine this issue template or add any additional details before you submit it to GitHub?