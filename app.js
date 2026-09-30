<!DOCTYPE html>
<html lang="zh-Hant-TW">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, shrink-to-fit=no">
    <title>臺北市政府消防局行政罰查網</title>
    <link rel="stylesheet" href="https://210.69.42.55/css/bootstrap.min.css">
    <link rel="stylesheet" href="https://210.69.42.55/3rdPart/font-awesome-4.7.0/css/font-awesome.min.css">
    <link rel="stylesheet" href="https://210.69.42.55/css/main.css">
    <!--[if lt IE 9]>
    <script src="https://210.69.42.55/js/html5shiv.min.js"></script>
    <script src="https://210.69.42.55/js/respond.min.js"></script>
    <![endif]-->
</head>
<body>
<div class="container-fluid">
    <div class="row menu">
        <div class="con-sm-12">
            <nav class="navbar navbar-default" role="navigation">
                <div class="container">
                    <div class="navbar-header">
                        <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-ex1-collapse">
                            <span class="sr-only">切換導覽</span>
                            <span class="icon-bar"></span>
                            <span class="icon-bar"></span>
                            <span class="icon-bar"></span>
                        </button>
                        <a href="https://210.69.42.55">
                            <img src="https://210.69.42.55/images/titleLogo.png" width="280" alt="臺北市政府消防局行政罰查網">
                        </a>
                    </div>
                    <div class="collapse navbar-collapse navbar-ex1-collapse">
                        <ul class="nav navbar-nav">
                            <li><a href="https://210.69.42.55">查詢</a></li>
                        </ul>
                    </div>
                </div>
            </nav>
        </div>
    </div>

        <main class="homeLookup">
        <div class="container">
            <section class="lookupCard" aria-labelledby="lookup-title">
                <div class="lookupBadge"><i class="fa fa-shield" aria-hidden="true"></i> 線上繳費服務</div>
                <h1 id="lookup-title">繳費資料查詢</h1>
                <p class="lookupIntro">請輸入身分識別碼或繳費編號，查詢可繳費帳單並前往 PAY.TAIPEI 完成繳費。</p>

                <form class="lookupForm" role="search" method="POST" action="https://210.69.42.55/showList">
                    <input type="hidden" name="_token" value="rFj9oFTu2hHtxsYdgBrMedxs0KOjPcpBsoWBfhk6" autocomplete="off">                    <label for="search">身分識別碼或繳費編號</label>
                    <div class="lookupControl">
                        <div class="lookupInputWrap">
                            <i class="fa fa-search" aria-hidden="true"></i>
                            <input type="text" class="form-control" id="search" name="search" value=""
                                   placeholder="請輸入身分識別碼或繳費編號" maxlength="50" autocomplete="off" required>
                        </div>
                        <button type="submit" class="btn lookupSubmit">開始查詢</button>
                    </div>
                </form>

                            </section>

            <section class="lookupSteps" aria-label="繳費流程">
                <div class="lookupStep">
                    <span class="stepNumber">1</span>
                    <i class="fa fa-keyboard-o" aria-hidden="true"></i>
                    <div><h2>輸入資料</h2><p>輸入識別碼或繳費編號。</p></div>
                </div>
                <div class="lookupStep">
                    <span class="stepNumber">2</span>
                    <i class="fa fa-file-text-o" aria-hidden="true"></i>
                    <div><h2>確認帳單</h2><p>核對繳費項目與金額。</p></div>
                </div>
                <div class="lookupStep">
                    <span class="stepNumber">3</span>
                    <i class="fa fa-external-link" aria-hidden="true"></i>
                    <div><h2>前往繳費</h2><p>透過 PAY.TAIPEI 安全繳費。</p></div>
                </div>
            </section>

            <aside class="lookupSecurity">
                <i class="fa fa-lock" aria-hidden="true"></i>
                <div><strong>資料安全與隱私</strong><span>查詢結果僅供繳費驗證使用，畫面不會顯示完整個人資料。</span></div>
            </aside>

            <section class="lookupHelp">
                <div><i class="fa fa-info-circle" aria-hidden="true"></i><strong>查詢提醒</strong><span>請依通知單所載資料輸入，並再次核對帳單內容。</span></div>
                <div><i class="fa fa-clock-o" aria-hidden="true"></i><strong>線上服務</strong><span>網站全年提供查詢；實際繳費狀態以 PAY.TAIPEI 回傳結果為準。</span></div>
            </section>
        </div>
    </main>
</div>

<script src="https://210.69.42.55/js/jquery.js"></script>
<script src="https://210.69.42.55/js/bootstrap.min.js"></script>
</body>
</html>
