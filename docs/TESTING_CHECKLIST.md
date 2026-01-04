# Testing Checklist

Use this checklist to verify the application is working correctly.

## ✅ Initial Setup

- [ ] Run `./setup.sh` successfully
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env file created with SECRET_KEY
- [ ] Class icons generated in `app/static/img/classes/`
- [ ] Database initialized (scheduler.db created)
- [ ] Test user created (optional)

## ✅ Application Startup

- [ ] Activate virtual environment: `source venv/bin/activate`
- [ ] Start app: `python run.py`
- [ ] No errors in console
- [ ] App accessible at http://localhost:5000

## ✅ Home Page

- [ ] Home page loads
- [ ] Bootstrap styling applied
- [ ] Navigation bar visible
- [ ] Login/Signup links work (when not logged in)

## ✅ User Registration

- [ ] Navigate to Signup
- [ ] Form displays correctly
- [ ] All 9 classes in dropdown
- [ ] Role checkboxes visible (tank/healer/dps)
- [ ] Create first user (should become superuser)
- [ ] Redirected after signup
- [ ] Flash message shows "Welcome, [character]!"
- [ ] Navigation shows character name

## ✅ User Login

- [ ] Logout
- [ ] Navigate to Login
- [ ] Form displays correctly
- [ ] Login with correct credentials works
- [ ] Login with wrong credentials fails with error message
- [ ] "Remember me" persists session

## ✅ My Availability Page

- [ ] Navigate to "My Availability"
- [ ] Date range picker visible
- [ ] Default dates set (today + 7 days)
- [ ] Selection mode buttons visible
- [ ] Click "Load Availability"
- [ ] Timeline grid renders
- [ ] Can select different modes (Available/Maybe/Unavailable)
- [ ] Click and drag works to paint cells
- [ ] Colors match selection mode
- [ ] "Save Changes" button saves without errors
- [ ] Reload page - saved availability persists

## ✅ Guild Timeline

- [ ] Create a second test user account
- [ ] Set some availability for both users
- [ ] Navigate to "Guild Timeline"
- [ ] Date range selector works
- [ ] Class filter dropdown works
- [ ] Role filter dropdown works
- [ ] Confidence filter works
- [ ] Sort options work (alphabetical/most available/by class)
- [ ] Click "Load Timeline"
- [ ] Timeline shows both users
- [ ] Class icons display correctly
- [ ] Role badges display correctly
- [ ] Cell colors match availability states
- [ ] Hover over cells shows tooltips (desktop)

## ✅ Heatmap View

- [ ] Navigate to "Heatmap"
- [ ] Date range selector works
- [ ] Click "Load Heatmap"
- [ ] Grid renders with color intensity
- [ ] Higher availability = darker green
- [ ] Click on cell shows count in tooltip
- [ ] Legend displays correctly

## ✅ Mobile Responsive

- [ ] Resize browser to mobile width (<768px)
- [ ] Navigation collapses to hamburger menu
- [ ] Timeline view shows accordion
- [ ] Accordion items expand/collapse
- [ ] My Availability still usable

## ✅ Admin Panel (Superuser Only)

- [ ] Login as first user (superuser)
- [ ] "Admin" link visible in navigation
- [ ] Navigate to Admin Panel
- [ ] User list displays
- [ ] Class icons visible
- [ ] Role badges visible
- [ ] Can promote second user to admin
- [ ] Promotion successful, page reloads
- [ ] "Demote" button now visible for second user
- [ ] Click "Download Roster CSV"
- [ ] CSV file downloads
- [ ] CSV contains correct data

## ✅ Security Features

- [ ] Try accessing /admin without login → Redirected to login
- [ ] Try accessing /api/me without login → 401 error
- [ ] CSRF token present in forms (view page source)
- [ ] Rapid signups trigger rate limit (try 6 signups quickly)
- [ ] Session persists after browser close (if remember me checked)
- [ ] Logout clears session

## ✅ Error Handling

- [ ] Enter invalid date range → Error message
- [ ] Submit empty signup form → Validation errors
- [ ] Try duplicate character name → Error message
- [ ] Wrong password on login → Error message
- [ ] Invalid AJAX request → Proper error response

## ✅ Docker Deployment (Optional)

- [ ] Class icons exist before building
- [ ] `docker-compose up -d` builds successfully
- [ ] `docker-compose exec web python init_db.py` works
- [ ] Application accessible at http://localhost:5000
- [ ] Data persists after `docker-compose restart`
- [ ] `docker-compose logs -f` shows no errors

## ✅ Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari (Mac)
- [ ] Edge

## ✅ Timezone Functionality

- [ ] Check browser console for timezone detection
- [ ] Set availability at a specific time
- [ ] Check database (slot_index should be UTC-based integer)
- [ ] View on another device/timezone (should convert correctly)

## 🐛 Common Issues & Solutions

### "ModuleNotFoundError: No module named 'flask'"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Class icons not showing
```bash
python3 create_icons.py
```

### Database errors
```bash
rm scheduler.db
python init_db.py
```

### Port 5000 already in use
Edit `run.py`, change port to 5001 or another available port

### CSRF errors
Clear browser cache and cookies, restart application

### Timeline not loading
Check browser console for JavaScript errors
Verify date range is valid
Check that users have set availability

## 📝 Notes

After testing, document any issues found:

**Issues Found:**
- [ ] Issue 1: _______________
- [ ] Issue 2: _______________
- [ ] Issue 3: _______________

**Overall Status:**
- [ ] All features working
- [ ] Ready for production (with SSL/proper SECRET_KEY)
- [ ] Needs fixes (list above)

**Performance Notes:**
- Page load time: _______
- Timeline render time: _______
- Availability save time: _______

---

**Tester**: _______________
**Date**: _______________
**Environment**: Development / Docker / Production
**Browser**: _______________
**OS**: _______________
