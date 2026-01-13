# Session Context: UI Redesign (2026-01-13)

## Objective
Apply Apple-inspired UI design system across the entire Dragofactu application.

## Work Completed

### 1. Created Centralized Stylesheet
**File:** `dragofactu/ui/styles.py`

Created a comprehensive Qt stylesheet implementing the design system with:
- Color palette constants (COLORS dict)
- Typography settings (FONTS dict)
- Spacing values (SPACING dict)
- Border radius values (RADIUS dict)
- `get_base_stylesheet()` - Returns full app stylesheet
- `apply_stylesheet(app)` - One-liner to apply to QApplication
- Helper functions for cards, buttons (primary/secondary/danger)

### 2. Added UIStyles Class to Monolithic App
**File:** `dragofactu_complete.py` (lines 39-262)

Added `UIStyles` class with:
- `COLORS` - All color tokens
- `get_panel_style()` - Tab backgrounds
- `get_card_style()` - Card containers
- `get_primary_button_style()` - Blue filled buttons
- `get_secondary_button_style()` - Outline buttons
- `get_danger_button_style()` - Red delete buttons
- `get_table_style()` - Clean tables with hover
- `get_input_style()` - Form inputs
- `get_section_title_style()` - 17px section headers
- `get_label_style()` - Form labels
- `get_status_label_style()` - Footer status
- `get_group_box_style()` - Grouped sections
- `get_dialog_style()` - Dialog backgrounds
- `get_toolbar_button_style()` - Small icon buttons

### 3. Updated Dashboard
**File:** `dragofactu_complete.py` - `Dashboard` class

- Welcome section with greeting
- 4 metric cards (Clients, Products, Documents, Low Stock)
- Quick action cards with hover effects
- Recent documents list from database
- Clean white cards with light borders

### 4. Updated MainWindow
**File:** `dragofactu_complete.py` - `MainWindow` class

- Modern menu bar styling
- Clean tab styling with accent underline
- Status bar with user info
- Removed all emojis from menus
- Added keyboard shortcuts (Ctrl+Shift+P, Ctrl+Shift+F, etc.)

### 5. Updated All Management Tabs

#### ClientManagementTab
- Page title "Clientes" (28px)
- Primary button "+ Nuevo Cliente"
- Secondary buttons "Editar", "Actualizar"
- Danger button "Eliminar"
- Search input with placeholder
- Clean table with uppercase headers

#### ProductManagementTab
- Same pattern as ClientManagementTab
- Page title "Productos"

#### DocumentManagementTab
- Page title "Documentos"
- Filter dropdown styled
- Primary button for Invoice (most common action)

#### InventoryManagementTab
- Page title "Inventario"
- Stats cards with colored borders (Total, Low Stock, Value)
- Search + filter combo

#### DiaryManagementTab
- Page title "Diario"
- Notes in white card container
- Date picker styled
- Stats badges for notes count

### 6. Updated LoginDialog
- Card-based form layout
- Labeled inputs (not placeholders only)
- Centered design
- Fixed size 400x420

### 7. Menu Cleanup
- Removed all emojis
- Added standard shortcuts:
  - Ctrl+Shift+P - New Quote
  - Ctrl+Shift+F - New Invoice
  - Ctrl+I - Import
  - Ctrl+E - Export
  - Ctrl+Q - Quit
  - Ctrl+, - Preferences

## Files Modified

| File | Changes |
|------|---------|
| `dragofactu/ui/styles.py` | NEW - Centralized stylesheet |
| `dragofactu_complete.py` | UIStyles class, all UI components updated |
| `CLAUDE.md` | Updated with full design system documentation |

## Design Tokens Applied

```
Background:     #FAFAFA
Cards:          #FFFFFF
Hover:          #F5F5F7
Text Primary:   #1D1D1F
Text Secondary: #6E6E73
Text Tertiary:  #86868B
Accent:         #007AFF
Success:        #34C759
Warning:        #FF9500
Danger:         #FF3B30
Border:         #D2D2D7
Border Light:   #E5E5EA
```

## Patterns Established

1. **Page Headers**: 28px, weight 600, primary color
2. **Section Titles**: 17px, weight 600, primary color
3. **Buttons**: Primary (accent), Secondary (outline), Danger (red)
4. **Tables**: No grid, uppercase headers, hover rows
5. **Cards**: White bg, 1px light border, 12px radius
6. **Inputs**: 8px radius, focus border accent
7. **Stats Badges**: Card style with semantic border colors

## Next Steps (Not Done)

- [ ] Update ClientDialog, ProductDialog, DocumentDialog styling
- [ ] Update SettingsDialog styling
- [ ] Update DiaryEntryDialog styling
- [ ] Add loading states/spinners
- [ ] Add toast notifications instead of QMessageBox
- [ ] Consider adding icons (SF Symbols style)

## Testing

Run the application to verify:
```bash
python3 dragofactu_complete.py
```

Login with: `admin` / `admin123`
