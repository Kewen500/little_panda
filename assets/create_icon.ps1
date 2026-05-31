Add-Type -AssemblyName System.Drawing

$assetsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pngPath = Join-Path $assetsDir "api-balance-widget.png"
$icoPath = Join-Path $assetsDir "api-balance-widget.ico"

function New-RoundedRectangle {
    param(
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )

    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $diameter = $Radius * 2
    $path.AddArc($X, $Y, $diameter, $diameter, 180, 90)
    $path.AddArc($X + $Width - $diameter, $Y, $diameter, $diameter, 270, 90)
    $path.AddArc(
        $X + $Width - $diameter,
        $Y + $Height - $diameter,
        $diameter,
        $diameter,
        0,
        90
    )
    $path.AddArc($X, $Y + $Height - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()
    return $path
}

$bitmap = [System.Drawing.Bitmap]::new(256, 256)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
$graphics.Clear([System.Drawing.Color]::Transparent)

$outerPath = New-RoundedRectangle 18 18 220 220 52
$outerBrush = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
    [System.Drawing.RectangleF]::new(18, 18, 220, 220),
    [System.Drawing.Color]::FromArgb(255, 13, 27, 42),
    [System.Drawing.Color]::FromArgb(255, 25, 57, 78),
    45
)
$graphics.FillPath($outerBrush, $outerPath)

$glowPath = New-RoundedRectangle 31 31 194 194 43
$glowPen = [System.Drawing.Pen]::new(
    [System.Drawing.Color]::FromArgb(88, 94, 234, 212),
    3
)
$graphics.DrawPath($glowPen, $glowPath)

$cardPath = New-RoundedRectangle 51 56 154 142 26
$cardBrush = [System.Drawing.SolidBrush]::new(
    [System.Drawing.Color]::FromArgb(255, 239, 250, 252)
)
$graphics.FillPath($cardBrush, $cardPath)

$stripeBrush = [System.Drawing.SolidBrush]::new(
    [System.Drawing.Color]::FromArgb(255, 25, 173, 189)
)
$stripePath = New-RoundedRectangle 51 56 154 35 25
$graphics.FillPath($stripeBrush, $stripePath)
$graphics.FillRectangle($stripeBrush, 51, 73, 154, 18)

$coinBrush = [System.Drawing.SolidBrush]::new(
    [System.Drawing.Color]::FromArgb(255, 245, 183, 66)
)
$graphics.FillEllipse($coinBrush, 72, 111, 54, 54)
$coinPen = [System.Drawing.Pen]::new(
    [System.Drawing.Color]::FromArgb(255, 212, 139, 35),
    4
)
$graphics.DrawEllipse($coinPen, 72, 111, 54, 54)
$coinFont = [System.Drawing.Font]::new(
    "Arial",
    27,
    [System.Drawing.FontStyle]::Bold,
    [System.Drawing.GraphicsUnit]::Pixel
)
$coinTextBrush = [System.Drawing.SolidBrush]::new(
    [System.Drawing.Color]::FromArgb(255, 129, 82, 18)
)
$graphics.DrawString(
    [char]0x00A5,
    $coinFont,
    $coinTextBrush,
    [System.Drawing.PointF]::new(84, 121)
)

$linePen = [System.Drawing.Pen]::new(
    [System.Drawing.Color]::FromArgb(255, 21, 147, 156),
    8
)
$linePen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
$linePen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
$graphics.DrawLine($linePen, 143, 158, 161, 138)
$graphics.DrawLine($linePen, 161, 138, 178, 151)
$graphics.DrawLine($linePen, 178, 151, 193, 124)
$graphics.DrawLine($linePen, 179, 124, 193, 124)
$graphics.DrawLine($linePen, 193, 124, 193, 138)

$bitmap.Save($pngPath, [System.Drawing.Imaging.ImageFormat]::Png)
$iconHandle = $bitmap.GetHicon()
$icon = [System.Drawing.Icon]::FromHandle($iconHandle)
$stream = [System.IO.File]::Create($icoPath)
$icon.Save($stream)
$stream.Close()

$icon.Dispose()
$bitmap.Dispose()
$graphics.Dispose()
$outerBrush.Dispose()
$outerPath.Dispose()
$glowPen.Dispose()
$glowPath.Dispose()
$cardBrush.Dispose()
$cardPath.Dispose()
$stripeBrush.Dispose()
$stripePath.Dispose()
$coinBrush.Dispose()
$coinPen.Dispose()
$coinFont.Dispose()
$coinTextBrush.Dispose()
$linePen.Dispose()

Write-Output $icoPath
