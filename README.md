# AutoGuard

Dynamic Compliance Checking for Android Automotive Apps

List of all rules of Google’s Car App Quality Guidelines in AutoGuard. The specific rules mentioned in this paper have been bolded.

![List of all tested rules of Google’s Car App Quality Guidelines in AutoGuard.](https://github.com/AutoGuard2026/AutoGuard/blob/main/guidelines.png)

<img src="https://github.com/AutoGuard2026/AutoGuard/blob/main/guidelines2.png">

## setup

```
pip install -r requirements.txt
```

Download the Android Debug Bridge (ADB).

Modify the `test_name` and `app_type` parameters in `run.py` to the values of the application under test, and update the `api_key` as well.

Run `run.py` with Python to start using the tool.

### AAOS

Install Android Studio and the in-vehicle emulator.

### Android Auto

Install the DHU.

- Prepare a phone, install the Android Auto app, and start Developer Mode.
