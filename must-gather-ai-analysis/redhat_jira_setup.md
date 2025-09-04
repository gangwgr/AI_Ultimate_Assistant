# 🔴 Red Hat Jira Integration Setup

## ✅ Great News for Red Hat Users!

Your **Red Hat Jira instance** supports **password authentication** - no API tokens needed!

## 🔧 Quick Setup for Red Hat Jira

### **Step 1: Open AI Assistant Builder**
Visit: http://localhost:8503

### **Step 2: Go to Jira Integration Tab**
- Click on **"Jira Integration"** tab
- You'll see Red Hat-specific guidance

### **Step 3: Enter Your Red Hat Credentials**

```
Server URL: https://issues.redhat.com
Username:   [Your Red Hat username] (e.g., rsmith)
Password:   [Your Red Hat password]
```

**Important:**
- ✅ Use your **Red Hat username** (not email)
- ✅ Use your **regular Red Hat password**
- ❌ **No API token needed!**

### **Step 4: Test Connection**
1. Click "Save Configuration"
2. Click "Test Connection"
3. Should show: ✅ Connected successfully as [Your Name]

### **Step 5: Fetch Your Issues**
- Select issue type: "Assigned to Me", "QA Contact", "Reported by Me", etc.
- Click "Fetch Issues"
- Generate training data for AI assistance

## 🗣️ Natural Language Commands

Once configured, use these commands in the chatbot (http://localhost:8502):

- `"Add comment to RHEL-12345 saying testing completed"`
- `"Mark RHEL-12345 as done"`
- `"Find issues with authentication"`
- `"Show my assigned issues"`

## 🛠️ Troubleshooting

**If connection fails:**
1. **Double-check username** - use Red Hat username, not email
2. **Verify password** - try logging into https://issues.redhat.com manually
3. **Check VPN** - Red Hat's Jira may require VPN access
4. **Contact IT** - if you get permission errors

## 🎯 Why Red Hat is Different

**Red Hat's Internal Systems:**
- ✅ **Self-hosted Jira** (not Atlassian Cloud)
- ✅ **Password authentication enabled**
- ✅ **No SSO complexity** for API access
- ✅ **Direct LDAP/Kerberos integration**

**vs Atlassian Cloud:**
- ❌ Passwords disabled for security
- ❌ API tokens required
- ❌ Complex SSO setup

## 🚀 You're All Set!

Red Hat Jira users have the **easiest setup** - just username and password! 🎉 