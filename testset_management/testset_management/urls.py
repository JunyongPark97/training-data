
from django.contrib import admin
from django.urls import path, include
from testset import views as testset_views
from source import views as source_views
from hangul_qalculator import views as qalculator_views
from picture_boxing import views as boxing_views
from handwritten import views as handwritten_views
from training import views as training_views

from rest_framework.routers import SimpleRouter


router = SimpleRouter()
router.register(r'testset/box', testset_views.BoxViewSet)
router.register(r'testset', testset_views.TestSetViewSet)
router.register(r'source/box', source_views.OCRSearchRequestBoxViewSet)
router.register(r'qalculator/box', qalculator_views.QalculatorBoxViewSet)
router.register(r'qalculator', qalculator_views.QalculatorSourceViewSet)
router.register(r'boxing/box', boxing_views.BoxViewSet)
router.register(r'boxing', boxing_views.SourceViewSet)

router.register(r'handwritten/source/box', handwritten_views.HandwrittenBoxViewSet)
router.register(r'handwritten/source', handwritten_views.HandwrittenSourceViewSet)
router.register(r'handwritten/testset/box', handwritten_views.BoxViewSet)
router.register(r'handwritten/testset', handwritten_views.HandwrittenTestsetViewSet)
router.register(r'box', training_views.BoxReadViewSet),
# path('box/', training_views.BoxReadViewSet.as_view(), name='box'),

router.register(r'training/box', training_views.BoxViewSet)
router.register(r'training', training_views.OCRSearchRequestSourceList)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('', testset_views.index, name="main"),
    path('testset/<int:pk>', testset_views.TestSetDetailView.as_view(), name='testset-boxing-detail'),
    path('source/ocrsr/<int:pk>', source_views.OCRSearchRequestSourceDetailView.as_view(), name='source-detail'),
    path('qalculator/source/<int:pk>', qalculator_views.QalculatorSourceDetailView.as_view(), name='qalculator-detail'),
    path('boxing/source/<int:pk>', boxing_views.SourceDetailView.as_view(), name='boxing-detail'),
    # path('box/', training_views.BoxReadViewSet.as_view(), name='box'),
    # path('box/<hangul>', training_views.BoxHangulList.as_view({'get': 'list'}), name='box'),
    # path('training/', training_views.OCRSearchRequestSourceList.as_view(), name='box'),

    path('handwritten/source/<int:pk>', handwritten_views.HandwrittenSourceDetailView.as_view(), name='handwritten-source-detail'),
    path('handwritten/testset/<int:pk>', handwritten_views.HandwrittenTestsetDetailView.as_view(), name='handwritten-testset-detail'),

    path('training/ocrsr/<int:pk>', training_views.OCRSearchRequestSourceBoxingView.as_view(), name='training-ocrsr-detail'),
    path('pictureboxing/word-box/<int:pk>', boxing_views.call_word_box, name='call-word-box'),


    path('api/', include(router.urls)),
]
