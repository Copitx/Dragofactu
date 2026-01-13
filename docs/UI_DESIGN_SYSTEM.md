# Dragofactu UI Design System

A modern, Apple-inspired visual system for PySide6/Qt desktop application.

---

## Color Palette

### Light Theme (Primary)

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Background Primary** | Off-white | `#FAFAFA` | Main window, content areas |
| **Background Secondary** | Light gray | `#F5F5F7` | Sidebars, panels, cards |
| **Background Tertiary** | White | `#FFFFFF` | Inputs, elevated cards, dialogs |
| **Surface Hover** | Subtle gray | `#E8E8ED` | Hover states on interactive elements |
| **Surface Active** | Light blue tint | `#E3F2FD` | Selected/active items |
| **Border Primary** | Soft gray | `#D2D2D7` | Card borders, separators |
| **Border Secondary** | Lighter gray | `#E5E5EA` | Subtle dividers |

### Text Colors

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Text Primary** | Near black | `#1D1D1F` | Headlines, primary content |
| **Text Secondary** | Dark gray | `#6E6E73` | Descriptions, secondary info |
| **Text Tertiary** | Medium gray | `#8E8E93` | Placeholders, disabled text |
| **Text Inverse** | White | `#FFFFFF` | Text on dark/accent backgrounds |

### Accent Colors

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| **Accent Primary** | Apple Blue | `#007AFF` | Primary actions, links, focus |
| **Accent Hover** | Darker blue | `#0056CC` | Hover state for primary |
| **Success** | Green | `#34C759` | Confirmations, positive states |
| **Warning** | Orange | `#FF9500` | Alerts, attention needed |
| **Danger** | Red | `#FF3B30` | Errors, destructive actions |
| **Info** | Teal | `#5AC8FA` | Informational badges |

### Status Colors (for documents/inventory)

| Status | Background | Text | Border |
|--------|------------|------|--------|
| Draft | `#F5F5F7` | `#6E6E73` | `#D2D2D7` |
| Sent | `#E3F2FD` | `#1976D2` | `#90CAF9` |
| Accepted | `#E8F5E9` | `#388E3C` | `#A5D6A7` |
| Paid | `#E8F5E9` | `#2E7D32` | `#81C784` |
| Partially Paid | `#FFF3E0` | `#F57C00` | `#FFCC80` |
| Rejected | `#FFEBEE` | `#C62828` | `#EF9A9A` |
| Low Stock | `#FFF3E0` | `#E65100` | `#FFCC80` |

---

## Typography

### Font Stack

```css
/* Primary: System fonts for native feel */
font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", "Helvetica Neue", Arial, sans-serif;

/* Monospace: For codes, numbers */
font-family: "SF Mono", "Menlo", "Monaco", "Consolas", monospace;
```

### Type Scale

| Level | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| **Display** | 28px | 600 | 1.2 | Page titles, dashboard headers |
| **H1** | 22px | 600 | 1.3 | Section headers |
| **H2** | 18px | 600 | 1.3 | Card titles, group headers |
| **H3** | 15px | 600 | 1.4 | Subsection headers |
| **Body** | 14px | 400 | 1.5 | Default text, descriptions |
| **Body Small** | 13px | 400 | 1.5 | Table content, secondary info |
| **Caption** | 12px | 400 | 1.4 | Labels, hints, metadata |
| **Overline** | 11px | 500 | 1.3 | Category labels (uppercase) |

### Font Weights
- **Regular**: 400 - Body text, descriptions
- **Medium**: 500 - Labels, emphasized text
- **Semibold**: 600 - Headers, buttons, important values

---

## Spacing System

Base unit: **4px**

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Tight spacing, icon gaps |
| `sm` | 8px | Inner padding, compact layouts |
| `md` | 12px | Standard padding, form gaps |
| `lg` | 16px | Section padding, card margins |
| `xl` | 24px | Major section gaps |
| `2xl` | 32px | Page margins, large separations |
| `3xl` | 48px | Dashboard card gaps |

### Layout Grid
- **Sidebar width**: 220px (collapsible to 60px)
- **Content max-width**: 1400px
- **Card gap**: 16px
- **Form field gap**: 12px vertical, 16px horizontal

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `none` | 0px | Tables, full-width elements |
| `sm` | 4px | Tags, badges, small buttons |
| `md` | 8px | Buttons, inputs, small cards |
| `lg` | 12px | Cards, panels, dialogs |
| `xl` | 16px | Large cards, modals |
| `full` | 9999px | Pills, avatars, circular buttons |

---

## Shadows

```css
/* Subtle elevation for cards */
shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);

/* Standard elevation for panels, dropdowns */
shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);

/* High elevation for modals, popovers */
shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);

/* Focus ring */
shadow-focus: 0 0 0 3px rgba(0, 122, 255, 0.3);
```

---

## Components

### Buttons

#### Primary Button
```css
QPushButton#primary {
    background-color: #007AFF;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#primary:hover {
    background-color: #0056CC;
}
QPushButton#primary:pressed {
    background-color: #004499;
}
QPushButton#primary:disabled {
    background-color: #B0B0B5;
}
```

#### Secondary Button
```css
QPushButton#secondary {
    background-color: #F5F5F7;
    color: #1D1D1F;
    border: 1px solid #D2D2D7;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 500;
}
QPushButton#secondary:hover {
    background-color: #E8E8ED;
    border-color: #C7C7CC;
}
```

#### Danger Button
```css
QPushButton#danger {
    background-color: #FF3B30;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#danger:hover {
    background-color: #D63029;
}
```

#### Ghost/Text Button
```css
QPushButton#ghost {
    background-color: transparent;
    color: #007AFF;
    border: none;
    padding: 8px 12px;
    font-size: 14px;
    font-weight: 500;
}
QPushButton#ghost:hover {
    background-color: rgba(0, 122, 255, 0.08);
    border-radius: 6px;
}
```

### Input Fields

```css
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #FFFFFF;
    color: #1D1D1F;
    border: 1px solid #D2D2D7;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 14px;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #007AFF;
    outline: none;
}

QLineEdit:disabled {
    background-color: #F5F5F7;
    color: #8E8E93;
}

/* Placeholder text */
QLineEdit::placeholder {
    color: #8E8E93;
}
```

### Cards / Panels

```css
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 12px;
    padding: 16px;
}

/* Elevated card (for important content) */
QFrame#cardElevated {
    background-color: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: 16px;
    /* Apply shadow via QGraphicsDropShadowEffect in code */
}

/* Stats card (dashboard) */
QFrame#statsCard {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 12px;
    padding: 20px;
    min-width: 200px;
}
```

### Tables

```css
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 8px;
    gridline-color: #F5F5F7;
    font-size: 13px;
}

QTableWidget::item {
    padding: 12px 16px;
    border-bottom: 1px solid #F5F5F7;
}

QTableWidget::item:selected {
    background-color: #E3F2FD;
    color: #1D1D1F;
}

QTableWidget::item:hover {
    background-color: #FAFAFA;
}

QHeaderView::section {
    background-color: #FAFAFA;
    color: #6E6E73;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    padding: 12px 16px;
    border: none;
    border-bottom: 1px solid #E5E5EA;
}
```

### Tabs

```css
QTabWidget::pane {
    border: none;
    background-color: #FAFAFA;
}

QTabBar::tab {
    background-color: transparent;
    color: #6E6E73;
    padding: 12px 20px;
    font-size: 14px;
    font-weight: 500;
    border: none;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:selected {
    color: #007AFF;
    border-bottom: 2px solid #007AFF;
}

QTabBar::tab:hover:!selected {
    color: #1D1D1F;
    background-color: #F5F5F7;
}
```

### Sidebar / Navigation

```css
QFrame#sidebar {
    background-color: #F5F5F7;
    border-right: 1px solid #E5E5EA;
    min-width: 220px;
}

QPushButton#navItem {
    background-color: transparent;
    color: #1D1D1F;
    text-align: left;
    padding: 12px 16px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    margin: 2px 8px;
}

QPushButton#navItem:hover {
    background-color: #E8E8ED;
}

QPushButton#navItem:checked, QPushButton#navItemActive {
    background-color: #FFFFFF;
    color: #007AFF;
    font-weight: 500;
}
```

### Status Badges

```css
QLabel#badgeDraft {
    background-color: #F5F5F7;
    color: #6E6E73;
    border: 1px solid #D2D2D7;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 500;
}

QLabel#badgePaid {
    background-color: #E8F5E9;
    color: #2E7D32;
    border: 1px solid #81C784;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 500;
}

QLabel#badgeWarning {
    background-color: #FFF3E0;
    color: #E65100;
    border: 1px solid #FFCC80;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 500;
}
```

### Dialogs / Modals

```css
QDialog {
    background-color: #FFFFFF;
    border-radius: 16px;
}

QDialog QLabel#dialogTitle {
    font-size: 18px;
    font-weight: 600;
    color: #1D1D1F;
    padding-bottom: 8px;
}

QDialog QLabel#dialogSubtitle {
    font-size: 14px;
    color: #6E6E73;
    padding-bottom: 16px;
}
```

### Scrollbars

```css
QScrollBar:vertical {
    background-color: transparent;
    width: 8px;
    margin: 4px;
}

QScrollBar::handle:vertical {
    background-color: #D2D2D7;
    border-radius: 4px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background-color: #B0B0B5;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: transparent;
    height: 8px;
    margin: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #D2D2D7;
    border-radius: 4px;
    min-width: 40px;
}
```

---

## Iconography Guidelines

- **Style**: SF Symbols-inspired, outline with 1.5px stroke
- **Size**: 16px (small), 20px (default), 24px (large)
- **Color**: Match text color or accent where appropriate
- **Library recommendation**: [Lucide Icons](https://lucide.dev) or [Feather Icons](https://feathericons.com)

---

## Animation Guidelines

| Property | Duration | Easing |
|----------|----------|--------|
| Color transitions | 150ms | ease-out |
| Hover states | 100ms | ease-out |
| Panel expand/collapse | 200ms | ease-in-out |
| Modal appear | 250ms | ease-out |
| Fade in/out | 150ms | ease |

---

## Application to Dragofactu

### Main Window
- Background: `#FAFAFA`
- Sidebar: `#F5F5F7` with white active items

### Dashboard
- Stats cards: White with subtle border, blue accent for values
- Quick action buttons: Primary blue style
- Activity feed: Subtle cards with timestamp in caption style

### Data Tables (Clients, Products, Documents)
- Alternating row colors: `#FFFFFF` / `#FAFAFA`
- Status badges inline in rows
- Sticky header with uppercase labels

### Forms (Add/Edit dialogs)
- Card-style form containers
- Grouped sections with H3 headers
- Primary action button right-aligned
- Cancel button as secondary/ghost

### Document States
Use status badge system consistently:
- Draft → Gray badge
- Sent → Blue badge
- Accepted/Paid → Green badge
- Warning states → Orange badge
- Errors → Red badge
