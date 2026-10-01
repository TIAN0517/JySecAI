# Generate a comprehensive admin password dictionary
bases = [
 'admin','password','admin123','admin123456','admin888','123456','12345678','123456789','1234567890',
 '12345','1234','111111','000000','666666','888888','654321','qwerty','abc123','a123456','a12345','1qaz2wsx',
 '1q2w3e4r','password1','password123','letmein','welcome','monkey','dragon','master','sunshine','princess',
 'charlie','shadow','superman','qazwsx','1qazxsw2','iloveyou','1111','2222','3333','6666','8888','admin@123',
 'admin@','admin@888','admin@123456','admin2024','admin2025','admin2026','admin2023','admin2022','admin2021',
 'unioncms','unionshop','shopadmin','adminshop','ofa77','ofa7777','ofa777','ofa1777','ofa888','ofa168','ofa666',
 'ofa123456','ofa123','ofa@123','ofaadmin','a888888','a123456789','123456a','123456a1','a1234567','123456789a',
 'ab123456','aa123456','123456aa','123456654321','admin1!','admin1!@','admin123!','admin123!@#','admin@1234',
 'admin666666','admin888888','admin000000','admin654321','admin1314520','1314520','123450','1234560','123456a.',
 'A123456','Aa123456','Aa123456!','Admin123','Admin@123','Admin123!','admin_123','admin123_','admin@1111',
 'admin@0000','admin@6666','admin@8888','admin@123456','admin12345','123456789a','1234567891','12345678901',
 '1314','520','5201314','1314520','999999','987654','121212','112233','666888','888666','168168','88866666',
 '1111111','88888888','66666666','00000000','1234567890a','a123456789','12345678901','1q2w3e','q1w2e3r4',
 '123abc','abc123456','123456abc','admin12345678','admin123456789','a1234567890','123456789012','pass123',
 'p@ssw0rd','p@ssword','password1234','iloveu','loveme','michael','jordan','harley','ranger','thomas','robert',
 'killer','george','andrew','joshua','chicken','pepper','daniel','banana','soccer','batman','trustno1','admin520',
 'admin666','admin168','admin2020','admin2019','admin2018','admin2017','admin8888','admin123!','Admin@123!',
 'admin@2024','admin@2025','admin@2026','admin@1777','17771777','1777admin','admin1777','ofa1777','ofa177777',
 '177717771777','ofa377','ofa37777','377377','377377377','admin377','shop123','shop123456','store123','mall123',
 'admin999','admin777','admin111','admin222','admin333','admin444','admin555','admin666','admin7777','admin88888',
]
extra = []
# patterns: prefix+number combos
for p in ['admin','ofa77','ofa','shop','123456','888888','666666']:
    for n in ['123','1234','12345','123456','2024','2025','2026','888','666','111','168','1777','377']:
        extra.append(p+n)
        extra.append(p+'@'+n)
        extra.append(p+n+'!')
        extra.append(p+'!'+n)
out = list(dict.fromkeys(bases+extra))
open('ofa77_pwds.txt','w').write('\n'.join(out))
print('total passwords:', len(out))
